from typing import List, Set
from sqlalchemy.orm import Session
import time

from app.models.playlist import Playlist, PlaylistType
from app.services.spotify_client import (
    get_artist,
    get_artist_top_tracks,
    search_playlists,
    get_playlist,
    get_playlist_tracks,
)


def classify_playlist(owner_id: str | None, name: str) -> PlaylistType:
    if owner_id == "spotify":
        return PlaylistType.EDITORIAL
    
    name_lower = name.lower()
    algorithmic_keywords = [
        "discover weekly",
        "release radar",
        "daily mix",
        "on repeat",
        "repeat rewind",
    ]
    
    if any(keyword in name_lower for keyword in algorithmic_keywords):
        return PlaylistType.ALGORITHMIC
    
    return PlaylistType.USER_GENERATED


def discover_playlists(artist_id: str, db: Session, max_playlists: int = 50) -> List[dict]:
    try:
        artist_data = get_artist(artist_id)
        artist_name = artist_data["name"]
    except Exception as e:
        print(f"Error getting artist {artist_id}: {e}")
        return []
    
    discovered = {}
    max_per_source = max_playlists // 2
    
    # Search by artist name
    search_by_artist = f'artist:"{artist_name}"'
    try:
        playlists_by_artist = search_playlists(search_by_artist, limit=max_per_source)
        print(f"Found {len(playlists_by_artist)} playlists by artist search")
    except Exception as e:
        print(f"Error searching playlists by artist: {e}")
        playlists_by_artist = []
    
    for playlist in playlists_by_artist:
        playlist_id = playlist.get("id")
        if playlist_id and playlist_id not in discovered:
            discovered[playlist_id] = playlist
    
    # Search by top tracks
    try:
        top_tracks = get_artist_top_tracks(artist_id, market="US")
        print(f"Found {len(top_tracks)} top tracks")
    except Exception as e:
        print(f"Error getting top tracks: {e}")
        top_tracks = []
    
    for track in top_tracks[:5]:
        track_name = track.get("name", "")
        if not track_name:
            continue
        search_query = f'track:"{track_name}" artist:"{artist_name}"'
        try:
            playlists_by_track = search_playlists(search_query, limit=10)
            print(f"Found {len(playlists_by_track)} playlists for track '{track_name}'")
        except Exception as e:
            print(f"Error searching playlists by track: {e}")
            playlists_by_track = []
        
        for playlist in playlists_by_track:
            playlist_id = playlist.get("id")
            if playlist_id and playlist_id not in discovered and len(discovered) < max_playlists:
                discovered[playlist_id] = playlist
                if len(discovered) >= max_playlists:
                    break
        
        if len(discovered) >= max_playlists:
            break
        time.sleep(0.05)  # Reduced delay
    
    print(f"Total discovered playlists before verification: {len(discovered)}")
    
    verified_playlists = []
    
    # Limit verification to reasonable number to avoid too many API calls
    max_to_verify = min(max_playlists, 50)  # Verify up to 50 playlists max
    
    def _artist_id_from_track_artist(track_artist: dict) -> str | None:
        """Extract artist id from track artist (id or uri like spotify:artist:xxx)."""
        if not track_artist:
            return None
        aid = track_artist.get("id")
        if aid:
            return str(aid)
        uri = track_artist.get("uri", "")
        if isinstance(uri, str) and "artist:" in uri:
            return uri.split("artist:")[-1].strip()
        return None
    
    for playlist_id, playlist_data in list(discovered.items())[:max_to_verify]:
        try:
            full_playlist = get_playlist(playlist_id)
            tracks = get_playlist_tracks(playlist_id, limit=100, artist_id=artist_id)
            # Total tracks in playlist (from API when available)
            total_tracks = full_playlist.get("tracks", {}).get("total")
            if total_tracks is not None:
                total_tracks = int(total_tracks)
            else:
                total_tracks = len(tracks) if tracks else 0
            
            # Count tracks that are by this artist (id or uri match).
            artist_id_str = str(artist_id)
            tracks_count = 0
            for track in tracks:
                if not track or not track.get("artists"):
                    continue
                for track_artist in track["artists"]:
                    tid = _artist_id_from_track_artist(track_artist)
                    if tid and tid == artist_id_str:
                        tracks_count += 1
                        break

            verified_playlists.append({
                "spotify_playlist_id": playlist_id,
                "name": full_playlist.get("name", "Unknown"),
                "owner_id": full_playlist.get("owner", {}).get("id"),
                "owner_name": full_playlist.get("owner", {}).get("display_name"),
                "follower_count": full_playlist.get("followers", {}).get("total", 0),
                "tracks_count": tracks_count,
                "total_tracks": total_tracks,
            })
            print(f"Included playlist: {full_playlist.get('name')} (total={total_tracks}, by artist={tracks_count})")
            
            if len(verified_playlists) >= max_playlists:
                break
            
            # Reduced delay - only 0.05s between playlist checks
            time.sleep(0.05)
        except Exception as e:
            print(f"Error verifying playlist {playlist_id}: {e}")
            continue
    
    print(f"Total verified playlists: {len(verified_playlists)}")
    return verified_playlists


def get_or_create_playlist(
    spotify_playlist_id: str,
    name: str,
    owner_id: str | None, 
    owner_name: str | None,
    follower_count: int | None,
    db: Session,
) -> Playlist:
    playlist = (
        db.query(Playlist)
        .filter(Playlist.spotify_playlist_id == spotify_playlist_id)
        .first()
    )
    
    if playlist:
        return playlist
    
    playlist_type = classify_playlist(owner_id, name)
    
    playlist = Playlist(
        spotify_playlist_id=spotify_playlist_id,
        name=name,
        owner_id=owner_id,
        owner_name=owner_name,
        playlist_type=playlist_type,
        follower_count=follower_count,
    )
    db.add(playlist)
    db.flush()
    return playlist
