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
    except Exception:
        return []
    
    discovered = {}
    max_per_source = max_playlists // 2
    
    search_by_artist = f'artist:"{artist_name}"'
    playlists_by_artist = search_playlists(search_by_artist, limit=max_per_source)
    
    for playlist in playlists_by_artist:
        playlist_id = playlist["id"]
        if playlist_id not in discovered:
            discovered[playlist_id] = playlist
    
    top_tracks = get_artist_top_tracks(artist_id, market="US")
    
    for track in top_tracks[:5]:
        track_name = track["name"]
        search_query = f'track:"{track_name}" artist:"{artist_name}"'
        playlists_by_track = search_playlists(search_query, limit=10)
        
        for playlist in playlists_by_track:
            playlist_id = playlist["id"]
            if playlist_id not in discovered and len(discovered) < max_playlists:
                discovered[playlist_id] = playlist
                if len(discovered) >= max_playlists:
                    break
        
        if len(discovered) >= max_playlists:
            break
        time.sleep(0.1)
    
    verified_playlists = []
    
    for playlist_id, playlist_data in list(discovered.items())[:max_playlists]:
        try:
            full_playlist = get_playlist(playlist_id)
            tracks = get_playlist_tracks(playlist_id, limit=100, artist_id=artist_id)
            
            artist_found = False
            tracks_count = 0
            
            for track in tracks:
                if track and track.get("artists"):
                    for track_artist in track["artists"]:
                        if track_artist and track_artist.get("id") == artist_id:
                            artist_found = True
                            tracks_count += 1
            
            if artist_found:
                verified_playlists.append({
                    "spotify_playlist_id": playlist_id,
                    "name": full_playlist["name"],
                    "owner_id": full_playlist["owner"].get("id"),
                    "owner_name": full_playlist["owner"].get("display_name"),
                    "follower_count": full_playlist.get("followers", {}).get("total"),
                    "tracks_count": tracks_count,
                })
            
            time.sleep(0.1)
        except Exception:
            continue
                
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
