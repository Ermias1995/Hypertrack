"""Mock Spotify client for development when Spotify app credentials are unavailable."""

from typing import List

_MOCK_PLAYLISTS = [
    {
        "id": "mock_pl_editorial_1",
        "name": "Today's Top Hits",
        "owner": {"id": "spotify", "display_name": "Spotify"},
        "followers": {"total": 32_000_000},
    },
    {
        "id": "mock_pl_editorial_2",
        "name": "Pop Rising",
        "owner": {"id": "spotify", "display_name": "Spotify"},
        "followers": {"total": 2_100_000},
    },
    {
        "id": "mock_pl_algo_1",
        "name": "Discover Weekly",
        "owner": {"id": "spotify", "display_name": "Spotify"},
        "followers": {"total": 0},
    },
    {
        "id": "mock_pl_user_1",
        "name": "Summer Vibes 2024",
        "owner": {"id": "user_abc", "display_name": "MusicFan"},
        "followers": {"total": 12_400},
    },
    {
        "id": "mock_pl_user_2",
        "name": "Chill Pop Mix",
        "owner": {"id": "user_xyz", "display_name": "CuratorDJ"},
        "followers": {"total": 8_200},
    },
]


def _short_name(spotify_id: str) -> str:
    if len(spotify_id) <= 12:
        return spotify_id
    return f"{spotify_id[:8]}…"


def get_artist(spotify_id: str) -> dict:
    return {
        "id": spotify_id,
        "name": f"Mock Artist ({_short_name(spotify_id)})",
    }


def get_artist_top_tracks(spotify_id: str, market: str = "US") -> List[dict]:
    name = _short_name(spotify_id)
    return [
        {"name": f"Hit One – {name}", "artists": [{"id": spotify_id, "name": f"Mock Artist ({name})"}]},
        {"name": f"Hit Two – {name}", "artists": [{"id": spotify_id, "name": f"Mock Artist ({name})"}]},
        {"name": f"Hit Three – {name}", "artists": [{"id": spotify_id, "name": f"Mock Artist ({name})"}]},
    ]


def search_playlists(query: str, limit: int = 50) -> List[dict]:
    return _MOCK_PLAYLISTS[: min(limit, len(_MOCK_PLAYLISTS))]


def get_playlist(playlist_id: str) -> dict:
    for p in _MOCK_PLAYLISTS:
        if p["id"] == playlist_id:
            return {
                "id": p["id"],
                "name": p["name"],
                "owner": p["owner"],
                "followers": p["followers"],
            }
    return {
        "id": playlist_id,
        "name": "Unknown Playlist",
        "owner": {"id": "unknown", "display_name": "Unknown"},
        "followers": {"total": 0},
    }


def get_playlist_tracks(
    playlist_id: str,
    limit: int = 100,
    artist_id: str | None = None,
) -> List[dict]:
    artist_id = artist_id or "mock_artist"
    name = _short_name(artist_id)
    count = 2 if "editorial" in playlist_id or "algo" in playlist_id else 3
    tracks = []
    for i in range(min(count, limit)):
        tracks.append({
            "id": f"mock_track_{playlist_id}_{i}",
            "name": f"Track {i + 1}",
            "artists": [{"id": artist_id, "name": f"Mock Artist ({name})"}],
        })
    return tracks
