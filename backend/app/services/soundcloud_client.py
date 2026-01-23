"""
SoundCloud API client for music discovery.
Implements the same interface as spotify_client for seamless integration.
"""

import base64
import requests
import time
from typing import List, Optional, Dict
from app.core.config import settings

BASE_URL = "https://api.soundcloud.com"
TOKEN_URL = "https://secure.soundcloud.com/oauth/token"

# Token state (in-memory, per process)
_access_token: Optional[str] = None
_refresh_token: Optional[str] = None
_token_expires_at: float = 0


def _get_access_token() -> str:
    """
    Get a valid SoundCloud access token.
    Reuses existing token if still valid, refreshes if needed, or gets new one.
    """
    global _access_token, _refresh_token, _token_expires_at
    
    # Check if we have a valid token (with 5 minute buffer)
    if _access_token and time.time() < (_token_expires_at - 300):
        return _access_token
    
    # Try to refresh if we have a refresh token
    if _refresh_token:
        try:
            return _refresh_access_token()
        except Exception:
            # Refresh failed, get new token
            pass
    
    # Get new token via Client Credentials
    if not settings.SOUNDCLOUD_CLIENT_ID or not settings.SOUNDCLOUD_CLIENT_SECRET:
        raise ValueError("SoundCloud credentials not configured")
    
    auth_str = f"{settings.SOUNDCLOUD_CLIENT_ID}:{settings.SOUNDCLOUD_CLIENT_SECRET}"
    b64 = base64.b64encode(auth_str.encode()).decode()
    
    response = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {b64}",
            "Content-Type": "application/x-www-form-urlencoded",
            "accept": "application/json; charset=utf-8",
        },
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    response.raise_for_status()
    
    data = response.json()
    _access_token = data["access_token"]
    _refresh_token = data.get("refresh_token")
    _token_expires_at = time.time() + data.get("expires_in", 3600) - 60
    
    return _access_token


def _refresh_access_token() -> str:
    """Refresh the access token using refresh_token."""
    global _access_token, _refresh_token, _token_expires_at
    
    if not _refresh_token:
        raise ValueError("No refresh token available")
    
    if not settings.SOUNDCLOUD_CLIENT_ID or not settings.SOUNDCLOUD_CLIENT_SECRET:
        raise ValueError("SoundCloud credentials not configured")
    
    response = requests.post(
        TOKEN_URL,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "accept": "application/json; charset=utf-8",
        },
        data={
            "grant_type": "refresh_token",
            "client_id": settings.SOUNDCLOUD_CLIENT_ID,
            "client_secret": settings.SOUNDCLOUD_CLIENT_SECRET,
            "refresh_token": _refresh_token,
        },
        timeout=10,
    )
    response.raise_for_status()
    
    data = response.json()
    _access_token = data["access_token"]
    _refresh_token = data.get("refresh_token")  # New refresh token (one-time use)
    _token_expires_at = time.time() + data.get("expires_in", 3600) - 60
    
    return _access_token


def _make_request(endpoint: str, params: dict = None, return_list: bool = False):
    """
    Make an authenticated request to SoundCloud API.
    return_list=True if endpoint returns a list directly (not wrapped in dict).
    """
    token = _get_access_token()
    url = f"{BASE_URL}{endpoint}"
    
    headers = {
        "Authorization": f"OAuth {token}",
        "accept": "application/json; charset=utf-8",
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        # SoundCloud sometimes returns lists directly, sometimes wrapped
        if return_list and isinstance(data, dict):
            # Check if it's a paginated response with collection
            return data.get("collection", data.get("data", []))
        return data
    except requests.exceptions.HTTPError as e:
        # If 401, try refreshing token once
        if e.response.status_code == 401:
            # Force refresh
            global _access_token
            _access_token = None
            token = _get_access_token()
            headers["Authorization"] = f"OAuth {token}"
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if return_list and isinstance(data, dict):
                return data.get("collection", data.get("data", []))
            return data
        raise


# Public API functions matching Spotify client interface

def get_artist(user_id: str) -> dict:
    """
    Get artist (user) information by SoundCloud user ID.
    Returns normalized format matching Spotify's artist response.
    """
    user = _make_request(f"/users/{user_id}")
    
    # Normalize to Spotify-like format
    return {
        "id": str(user.get("id", user_id)),
        "name": user.get("full_name") or user.get("username", "Unknown Artist"),
        "username": user.get("username"),
        "followers_count": user.get("followers_count", 0),
    }


def get_artist_top_tracks(user_id: str, market: str = "US") -> List[dict]:
    """
    Get top tracks by an artist (user).
    market parameter is ignored (SoundCloud is global).
    Returns normalized format matching Spotify's track response.
    """
    print(f"[SoundCloud] Getting top tracks for user: {user_id}")
    try:
        tracks_data = _make_request(f"/users/{user_id}/tracks", params={"limit": 200}, return_list=True)
        
        print(f"[SoundCloud] Raw tracks response type: {type(tracks_data)}")
        
        # Handle if it's a list or dict
        if isinstance(tracks_data, list):
            tracks = tracks_data
        elif isinstance(tracks_data, dict):
            tracks = tracks_data.get("collection", tracks_data.get("data", []))
        else:
            tracks = []
        
        print(f"[SoundCloud] Found {len(tracks)} tracks")
        
        # Sort by playback_count (popularity) descending
        sorted_tracks = sorted(
            tracks,
            key=lambda x: x.get("playback_count", 0),
            reverse=True
        )[:10]  # Top 10 tracks
    
        # Normalize to Spotify-like format
        result = []
        for track in sorted_tracks:
            if not isinstance(track, dict):
                continue
            track_user = track.get("user", {})
            result.append({
                "id": str(track.get("id")),
                "name": track.get("title", "Unknown Track"),
                "artists": [
                    {
                        "id": str(track_user.get("id", user_id)),
                        "name": track_user.get("full_name") or track_user.get("username", "Unknown Artist"),
                    }
                ],
                "duration": track.get("duration", 0),
                "playback_count": track.get("playback_count", 0),
            })
        
        print(f"[SoundCloud] Returning {len(result)} normalized tracks")
        return result
    except Exception as e:
        print(f"[SoundCloud] Error in get_artist_top_tracks: {e}")
        import traceback
        traceback.print_exc()
        return []


def search_playlists(query: str, limit: int = 50) -> List[dict]:
    """
    Search for playlists.
    query can be plain text (SoundCloud doesn't support advanced syntax).
    Returns normalized format matching Spotify's playlist response.
    """
    # Clean query - remove any Spotify-style syntax if present
    # e.g., 'artist:"Name"' -> 'Name', 'track:"Song" artist:"Name"' -> 'Song Name'
    clean_query = query.replace('artist:"', '').replace('track:"', '').replace('"', '').strip()
    # Remove extra spaces
    clean_query = ' '.join(clean_query.split())
    
    print(f"[SoundCloud] Searching playlists with query: '{clean_query}'")
    
    try:
        playlists_data = _make_request(
            "/playlists",
            params={"q": clean_query, "limit": limit},
            return_list=True
        )
        
        print(f"[SoundCloud] Raw response type: {type(playlists_data)}")
        if isinstance(playlists_data, dict):
            print(f"[SoundCloud] Response keys: {playlists_data.keys()}")
        
        # Handle if it's a list or dict
        if isinstance(playlists_data, list):
            playlists = playlists_data
        elif isinstance(playlists_data, dict):
            # SoundCloud might return paginated response
            playlists = playlists_data.get("collection", playlists_data.get("data", []))
            if not playlists:
                # Try direct access if it's a single playlist object
                if playlists_data.get("kind") == "playlist":
                    playlists = [playlists_data]
        else:
            playlists = []
        
        print(f"[SoundCloud] Found {len(playlists)} playlists after parsing")
        
        # Normalize to Spotify-like format
        result = []
        for playlist in playlists:
            if not isinstance(playlist, dict):
                continue
            owner = playlist.get("user", {})
            result.append({
                "id": str(playlist.get("id")),
                "name": playlist.get("title", "Unknown Playlist"),
                "owner": {
                    "id": str(owner.get("id", "unknown")),
                    "display_name": owner.get("full_name") or owner.get("username", "Unknown"),
                },
                "followers": {
                    "total": playlist.get("likes_count", 0) or playlist.get("followers_count", 0),
                },
                "description": playlist.get("description"),
            })
        
        print(f"[SoundCloud] Returning {len(result)} normalized playlists")
        return result
    except Exception as e:
        print(f"[SoundCloud] Error in search_playlists: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_playlist(playlist_id: str) -> dict:
    """
    Get playlist details by ID.
    Returns normalized format matching Spotify's playlist response.
    """
    print(f"[SoundCloud] Getting playlist: {playlist_id}")
    try:
        # Don't use show_tracks=false - we want tracks for verification
        playlist = _make_request(f"/playlists/{playlist_id}")
        
        owner = playlist.get("user", {})
        
        # Normalize to Spotify-like format
        result = {
            "id": str(playlist.get("id", playlist_id)),
            "name": playlist.get("title", "Unknown Playlist"),
            "owner": {
                "id": str(owner.get("id", "unknown")),
                "display_name": owner.get("full_name") or owner.get("username", "Unknown"),
            },
            "followers": {
                "total": playlist.get("likes_count", 0) or playlist.get("followers_count", 0),
            },
            "description": playlist.get("description"),
        }
        print(f"[SoundCloud] Retrieved playlist: {result['name']}")
        return result
    except Exception as e:
        print(f"[SoundCloud] Error in get_playlist: {e}")
        import traceback
        traceback.print_exc()
        raise


def get_playlist_tracks(
    playlist_id: str,
    limit: int = 100,
    artist_id: str | None = None,
) -> List[dict]:
    """
    Get tracks from a playlist.
    If artist_id is provided, filters tracks by that artist (user).
    Returns normalized format matching Spotify's track response.
    """
    print(f"[SoundCloud] Getting tracks for playlist: {playlist_id}, filtering by artist: {artist_id}")
    try:
        # Get playlist with tracks - need to request with tracks included
        playlist = _make_request(f"/playlists/{playlist_id}")
        tracks_data = playlist.get("tracks", [])
        
        print(f"[SoundCloud] Playlist response has {len(tracks_data)} tracks in 'tracks' field")
        
        # If tracks not in response, try tracks endpoint
        if not tracks_data:
            try:
                tracks_data = _make_request(f"/playlists/{playlist_id}/tracks", params={"limit": limit}, return_list=True)
                print(f"[SoundCloud] Tracks endpoint returned type: {type(tracks_data)}")
                # Handle if it's a list or dict
                if isinstance(tracks_data, dict):
                    tracks_data = tracks_data.get("collection", tracks_data.get("data", []))
            except Exception as e:
                print(f"[SoundCloud] Error getting tracks from endpoint: {e}")
                tracks_data = []
        
        # Ensure tracks_data is a list
        if not isinstance(tracks_data, list):
            print(f"[SoundCloud] tracks_data is not a list, converting...")
            tracks_data = []
        
        print(f"[SoundCloud] Processing {len(tracks_data)} tracks")
    
        # Normalize and filter
        result = []
        for track in tracks_data[:limit]:
            if not isinstance(track, dict):
                continue
            track_user = track.get("user", {})
            track_user_id = str(track_user.get("id", ""))
            
            # Filter by artist if specified
            if artist_id and track_user_id != str(artist_id):
                continue
            
            result.append({
                "id": str(track.get("id")),
                "name": track.get("title", "Unknown Track"),
                "artists": [
                    {
                        "id": track_user_id,
                        "name": track_user.get("full_name") or track_user.get("username", "Unknown Artist"),
                    }
                ],
                "duration": track.get("duration", 0),
            })
        
        print(f"[SoundCloud] Returning {len(result)} tracks (filtered by artist_id={artist_id})")
        return result
    except Exception as e:
        print(f"[SoundCloud] Error in get_playlist_tracks: {e}")
        import traceback
        traceback.print_exc()
        return []


def resolve_soundcloud_url(url: str) -> Optional[dict]:
    """
    Resolve a SoundCloud URL to get resource information.
    Returns dict with 'id' and 'kind' (user, playlist, track) or None if not found.
    """
    try:
        result = _make_request("/resolve", params={"url": url})
        return {
            "id": str(result.get("id")),
            "kind": result.get("kind"),  # "user", "playlist", "track"
            "data": result,  # Full response for reference
        }
    except Exception:
        return None
