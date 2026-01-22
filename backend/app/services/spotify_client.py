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
    return not (settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET)


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
    if _use_mock():
        from app.services.spotify_mock import get_artist as mock_get_artist
        return mock_get_artist(spotify_id)
    return _get_artist(spotify_id)


def get_artist_top_tracks(spotify_id: str, market: str = "US") -> List[dict]:
    if _use_mock():
        from app.services.spotify_mock import get_artist_top_tracks as mock_top
        return mock_top(spotify_id, market)
    return _get_artist_top_tracks(spotify_id, market)


def search_playlists(query: str, limit: int = 50) -> List[dict]:
    if _use_mock():
        from app.services.spotify_mock import search_playlists as mock_search
        return mock_search(query, limit)
    return _search_playlists(query, limit)


def get_playlist(playlist_id: str) -> dict:
    if _use_mock():
        from app.services.spotify_mock import get_playlist as mock_get_playlist
        return mock_get_playlist(playlist_id)
    return _get_playlist(playlist_id)


def get_playlist_tracks(
    playlist_id: str,
    limit: int = 100,
    artist_id: str | None = None,
) -> List[dict]:
    if _use_mock():
        from app.services.spotify_mock import get_playlist_tracks as mock_tracks
        return mock_tracks(playlist_id, limit, artist_id)
    return _get_playlist_tracks(playlist_id, limit, artist_id)
