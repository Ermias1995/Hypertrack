from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.artist import Artist
from app.models.snapshot import Snapshot
from app.models.placement import Placement
from app.models.playlist import Playlist
from app.schemas.artist import ArtistCreate, ArtistRead, ArtistQueryRequest, ArtistQueryResponse, PlaylistSummary
from app.schemas.snapshot import SnapshotRead
from app.services.discovery import discover_playlists, get_or_create_playlist
from app.services.diffing import calculate_changes
from app.services.spotify_client import get_artist as get_spotify_artist


router = APIRouter(prefix="/artists", tags=["artists"])


@router.post("/", response_model=ArtistRead)
def create_artist(payload: ArtistCreate, db: Session = Depends(get_db)):
    artist = Artist(
        spotify_artist_id=payload.spotify_artist_id,
        name=payload.name,
        spotify_url=payload.spotify_url,
    )
    db.add(artist)
    db.commit()
    db.refresh(artist)
    return artist


@router.get("/", response_model=list[ArtistRead])
def list_artists(db: Session = Depends(get_db)):
    return db.query(Artist).all()


@router.get("/{artist_id}", response_model=ArtistRead)
def get_artist(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )
    return artist


@router.get("/{artist_id}/history", response_model=list[SnapshotRead])
def get_artist_history(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )
    snapshots = (
        db.query(Snapshot)
        .filter(Snapshot.artist_id == artist_id)
        .order_by(Snapshot.snapshot_time.desc())
        .all()
    )
    return snapshots


@router.post("/query", response_model=ArtistQueryResponse)
def query_artist(payload: ArtistQueryRequest, db: Session = Depends(get_db)):
    url = payload.spotify_url.strip()
    spotify_id = url.rstrip("/").split("/")[-1].split("?")[0]

    artist = (
        db.query(Artist)
        .filter(Artist.spotify_artist_id == spotify_id)
        .first()
    )

    if artist and not payload.force_refresh:
        previous_snapshot = (
            db.query(Snapshot)
            .filter(Snapshot.artist_id == artist.id)
            .order_by(Snapshot.snapshot_time.desc())
            .first()
        )
        
        current_placements = (
            db.query(Placement)
            .filter(Placement.artist_id == artist.id)
            .filter(Placement.snapshot_id == previous_snapshot.id)
            .all() if previous_snapshot else []
        )
        
        current_playlists = []
        for placement in current_placements:
            playlist = db.query(Playlist).filter(Playlist.id == placement.playlist_id).first()
            if playlist:
                current_playlists.append(PlaylistSummary(
                    id=playlist.id,
                    name=playlist.name,
                    playlist_type=playlist.playlist_type.value if playlist.playlist_type else "user_generated",
                    tracks_count=placement.tracks_count,
                ))
        
        return ArtistQueryResponse(
            artist=artist,
            snapshot={
                "id": previous_snapshot.id if previous_snapshot else None,
                "snapshot_time": previous_snapshot.snapshot_time if previous_snapshot else None,
                "total_playlists_found": previous_snapshot.total_playlists_found if previous_snapshot else 0,
            },
            changes={"gained": [], "lost": []},
            current_playlists=current_playlists,
        )

    try:
        spotify_artist_data = get_spotify_artist(spotify_id)
        artist_name = spotify_artist_data["name"]
    except Exception:
        artist_name = spotify_id

    if not artist:
        artist = Artist(
            spotify_artist_id=spotify_id,
            name=artist_name,
            spotify_url=url,
        )
        db.add(artist)
        db.flush()

    if payload.force_refresh:
        artist.name = artist_name
        artist.spotify_url = url

    previous_snapshot = (
        db.query(Snapshot)
        .filter(Snapshot.artist_id == artist.id)
        .order_by(Snapshot.snapshot_time.desc())
        .first()
    )

    discovered_playlists = discover_playlists(spotify_id, db)
    
    snapshot = Snapshot(
        artist_id=artist.id,
        total_playlists_found=len(discovered_playlists),
        playlists_checked_count=len(discovered_playlists),
        discovery_method_used="hybrid",
    )
    db.add(snapshot)
    db.flush()
    
    artist.last_snapshot_at = snapshot.snapshot_time

    for playlist_data in discovered_playlists:
        playlist = get_or_create_playlist(
            spotify_playlist_id=playlist_data["spotify_playlist_id"],
            name=playlist_data["name"],
            owner_id=playlist_data.get("owner_id"),
            owner_name=playlist_data.get("owner_name"),
            follower_count=playlist_data.get("follower_count"),
            db=db,
        )

        placement = Placement(
            artist_id=artist.id,
            playlist_id=playlist.id,
            snapshot_id=snapshot.id,
            tracks_count=playlist_data.get("tracks_count", 1),
        )
        db.add(placement)

    db.commit()
    db.refresh(artist)
    db.refresh(snapshot)

    gained_ids, lost_ids = calculate_changes(
        previous_snapshot.id if previous_snapshot else None,
        snapshot.id,
        db,
    )

    gained_playlists = []
    for playlist_id in gained_ids:
        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        placement = db.query(Placement).filter(
            Placement.playlist_id == playlist_id,
            Placement.snapshot_id == snapshot.id
        ).first()
        if playlist and placement:
            gained_playlists.append(PlaylistSummary(
                id=playlist.id,
                name=playlist.name,
                playlist_type=playlist.playlist_type.value,
                tracks_count=placement.tracks_count,
            ))

    lost_playlists = []
    for playlist_id in lost_ids:
        playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
        if playlist:
            lost_playlists.append(PlaylistSummary(
                id=playlist.id,
                name=playlist.name,
                playlist_type=playlist.playlist_type.value if playlist.playlist_type else "user_generated",
                tracks_count=0,
            ))

    current_placements = (
        db.query(Placement)
        .filter(Placement.artist_id == artist.id)
        .filter(Placement.snapshot_id == snapshot.id)
        .all()
    )
    
    current_playlists = []
    for placement in current_placements:
        playlist = db.query(Playlist).filter(Playlist.id == placement.playlist_id).first()
        if playlist:
            current_playlists.append(PlaylistSummary(
                id=playlist.id,
                name=playlist.name,
                playlist_type=playlist.playlist_type.value if playlist.playlist_type else "user_generated",
                tracks_count=placement.tracks_count,
            ))

    return ArtistQueryResponse(
        artist=artist,
        snapshot={
            "id": snapshot.id,
            "snapshot_time": snapshot.snapshot_time,
            "total_playlists_found": snapshot.total_playlists_found,
        },
        changes={
            "gained": gained_playlists,
            "lost": lost_playlists,
        },
        current_playlists=current_playlists,
    )

