import base64
import requests
import time
from typing import List, Optional
from app.core.config import settings

TOKEN_URL = "https://accounts.spotify.com/api/token"
BASE_URL = "https://api.spotify.com/v1"

_access_token: Optional[str] = None
_token_expires_at: float = 0


def _use_mock() -> bool:
    """Check if we should use mock service."""
    return settings.MUSIC_API_PROVIDER.lower() == "mock"


def _use_soundcloud() -> bool:
    """Check if we should use SoundCloud API."""
    provider = settings.MUSIC_API_PROVIDER.lower()
    return provider == "soundcloud" and bool(
        settings.SOUNDCLOUD_CLIENT_ID and settings.SOUNDCLOUD_CLIENT_SECRET
    )


def _use_spotify() -> bool:
    """Check if we should use Spotify API."""
    provider = settings.MUSIC_API_PROVIDER.lower()
    return provider == "spotify" and bool(
        settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET
    )


def _get_access_token() -> str:
    global _access_token, _token_expires_at
    
    if _access_token and time.time() < _token_expires_at:
        return _access_token
    
    if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
        raise ValueError("Spotify credentials not configured")
    
    auth_str = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    b64 = base64.b64encode(auth_str.encode()).decode()
    
    response = requests.post(
        TOKEN_URL,
        data={"grant_type": "client_credentials"},
        headers={"Authorization": f"Basic {b64}"},
        timeout=10,
    )
    response.raise_for_status()
    
    data = response.json()
    _access_token = data["access_token"]
    _token_expires_at = time.time() + data.get("expires_in", 3600) - 60
    
    return _access_token


def _make_request(endpoint: str, params: dict = None) -> dict:
    token = _get_access_token()
    url = f"{BASE_URL}{endpoint}"
    
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def _get_artist(spotify_id: str) -> dict:
    return _make_request(f"/artists/{spotify_id}")


def _get_artist_top_tracks(spotify_id: str, market: str = "US") -> List[dict]:
    data = _make_request(f"/artists/{spotify_id}/top-tracks", params={"market": market})
    return data.get("tracks", [])


def _search_playlists(query: str, limit: int = 50) -> List[dict]:
    data = _make_request(
        "/search",
        params={
            "q": query,
            "type": "playlist",
            "limit": limit,
        },
    )
    return data.get("playlists", {}).get("items", [])


def _get_playlist(playlist_id: str) -> dict:
    return _make_request(f"/playlists/{playlist_id}")


def _get_playlist_tracks(
    playlist_id: str,
    limit: int = 100,
    artist_id: str | None = None,
) -> List[dict]:
    data = _make_request(
        f"/playlists/{playlist_id}/tracks",
        params={"limit": limit},
    )
    tracks = []
    for item in data.get("items", []):
        if item.get("track") and item["track"]:
            tracks.append(item["track"])
    return tracks


def get_artist(spotify_id: str) -> dict:
    """Get artist information. Works with Spotify IDs, SoundCloud user IDs, or mock."""
    if _use_mock():
        from app.services.spotify_mock import get_artist as mock_get_artist
        return mock_get_artist(spotify_id)
    elif _use_soundcloud():
        from app.services.soundcloud_client import get_artist as sc_get_artist
        return sc_get_artist(spotify_id)
    
    # Spotify API returns raw response
    data = _get_artist(spotify_id)
    
    # Extract image URL - Spotify returns images array, use medium or large
    image_url = None
    if data.get("images"):
        # Prefer medium (index 1) or large (index 0), fallback to first available
        for img in data["images"]:
            if img.get("height", 0) >= 300:  # Medium or large
                image_url = img.get("url")
                break
        if not image_url and len(data["images"]) > 0:
            image_url = data["images"][0].get("url")
    
    # Normalize to include image_url
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "image_url": image_url,
        "followers": data.get("followers", {}),
        "genres": data.get("genres", []),
    }


def get_artist_top_tracks(spotify_id: str, market: str = "US") -> List[dict]:
    """Get artist top tracks. Works with Spotify IDs, SoundCloud user IDs, or mock."""
    if _use_mock():
        from app.services.spotify_mock import get_artist_top_tracks as mock_top
        return mock_top(spotify_id, market)
    elif _use_soundcloud():
        from app.services.soundcloud_client import get_artist_top_tracks as sc_top
        return sc_top(spotify_id, market)
    return _get_artist_top_tracks(spotify_id, market)


def search_playlists(query: str, limit: int = 50) -> List[dict]:
    """Search for playlists. Works with Spotify, SoundCloud, or mock."""
    if _use_mock():
        from app.services.spotify_mock import search_playlists as mock_search
        return mock_search(query, limit)
    elif _use_soundcloud():
        from app.services.soundcloud_client import search_playlists as sc_search
        return sc_search(query, limit)
    return _search_playlists(query, limit)


def get_playlist(playlist_id: str) -> dict:
    """Get playlist details. Works with Spotify IDs, SoundCloud IDs, or mock."""
    if _use_mock():
        from app.services.spotify_mock import get_playlist as mock_get_playlist
        return mock_get_playlist(playlist_id)
    elif _use_soundcloud():
        from app.services.soundcloud_client import get_playlist as sc_get_playlist
        return sc_get_playlist(playlist_id)
    return _get_playlist(playlist_id)


def get_playlist_tracks(
    playlist_id: str,
    limit: int = 100,
    artist_id: str | None = None,
) -> List[dict]:
    """Get tracks from a playlist. Works with Spotify, SoundCloud, or mock."""
    if _use_mock():
        from app.services.spotify_mock import get_playlist_tracks as mock_tracks
        return mock_tracks(playlist_id, limit, artist_id)
    elif _use_soundcloud():
        from app.services.soundcloud_client import get_playlist_tracks as sc_tracks
        return sc_tracks(playlist_id, limit, artist_id)
    return _get_playlist_tracks(playlist_id, limit, artist_id)
