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


def _make_request(endpoint: str, params: dict = None) -> dict:
    """Make an authenticated request to SoundCloud API."""
    token = _get_access_token()
    url = f"{BASE_URL}{endpoint}"
    
    headers = {
        "Authorization": f"OAuth {token}",
        "accept": "application/json; charset=utf-8",
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
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
            return response.json()
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
    tracks = _make_request(f"/users/{user_id}/tracks", params={"limit": 200})
    
    # Sort by playback_count (popularity) descending
    sorted_tracks = sorted(
        tracks,
        key=lambda x: x.get("playback_count", 0),
        reverse=True
    )[:10]  # Top 10 tracks
    
    # Normalize to Spotify-like format
    result = []
    for track in sorted_tracks:
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
    
    return result


def search_playlists(query: str, limit: int = 50) -> List[dict]:
    """
    Search for playlists.
    query can be plain text (SoundCloud doesn't support advanced syntax).
    Returns normalized format matching Spotify's playlist response.
    """
    # Clean query - remove any Spotify-style syntax if present
    # e.g., 'artist:"Name"' -> 'Name'
    clean_query = query.replace('artist:"', '').replace('"', '').replace('track:"', '').strip()
    
    playlists = _make_request(
        "/playlists",
        params={"q": clean_query, "limit": limit}
    )
    
    # Normalize to Spotify-like format
    result = []
    for playlist in playlists:
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
    
    return result


def get_playlist(playlist_id: str) -> dict:
    """
    Get playlist details by ID.
    Returns normalized format matching Spotify's playlist response.
    """
    playlist = _make_request(f"/playlists/{playlist_id}", params={"show_tracks": "false"})
    
    owner = playlist.get("user", {})
    
    # Normalize to Spotify-like format
    return {
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
    # Get playlist with tracks
    playlist = _make_request(f"/playlists/{playlist_id}")
    tracks_data = playlist.get("tracks", [])
    
    # If tracks not in response, try tracks endpoint
    if not tracks_data:
        try:
            tracks_data = _make_request(f"/playlists/{playlist_id}/tracks", params={"limit": limit})
        except Exception:
            tracks_data = []
    
    # Normalize and filter
    result = []
    for track in tracks_data[:limit]:
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
    
    return result


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
