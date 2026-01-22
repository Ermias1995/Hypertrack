from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.artist import Artist
from app.models.snapshot import Snapshot
from app.models.placement import Placement
from app.models.playlist import Playlist
from app.schemas.artist import ArtistCreate, ArtistRead, ArtistQueryRequest, ArtistQueryResponse, PlaylistSummary
from app.schemas.snapshot import SnapshotRead, SnapshotWithChanges
from app.services.discovery import discover_playlists, get_or_create_playlist
from app.services.diffing import calculate_changes
from app.services.spotify_client import get_artist as get_spotify_artist


router = APIRouter(prefix="/artists", tags=["artists"])


def _playlist_type_str(playlist):
    return playlist.playlist_type.value if playlist.playlist_type else "user_generated"


def _placements_to_summaries(placements, db):
    out = []
    for p in placements:
        playlist = db.query(Playlist).filter(Playlist.id == p.playlist_id).first()
        if playlist:
            out.append(PlaylistSummary(
                id=playlist.id,
                name=playlist.name,
                playlist_type=_playlist_type_str(playlist),
                tracks_count=p.tracks_count,
            ))
    return out


def _run_discovery_and_respond(artist, db, update_name_from_spotify=True):
    spotify_id = artist.spotify_artist_id
    if update_name_from_spotify:
        try:
            data = get_spotify_artist(spotify_id)
            artist.name = data["name"]
        except Exception:
            pass

    previous = (
        db.query(Snapshot)
        .filter(Snapshot.artist_id == artist.id)
        .order_by(Snapshot.snapshot_time.desc())
        .first()
    )
    discovered = discover_playlists(spotify_id, db)

    snapshot = Snapshot(
        artist_id=artist.id,
        total_playlists_found=len(discovered),
        playlists_checked_count=len(discovered),
        discovery_method_used="hybrid",
    )
    db.add(snapshot)
    db.flush()
    artist.last_snapshot_at = snapshot.snapshot_time

    for pl in discovered:
        playlist = get_or_create_playlist(
            spotify_playlist_id=pl["spotify_playlist_id"],
            name=pl["name"],
            owner_id=pl.get("owner_id"),
            owner_name=pl.get("owner_name"),
            follower_count=pl.get("follower_count"),
            db=db,
        )
        placement = Placement(
            artist_id=artist.id,
            playlist_id=playlist.id,
            snapshot_id=snapshot.id,
            tracks_count=pl.get("tracks_count", 1),
        )
        db.add(placement)

    db.commit()
    db.refresh(artist)
    db.refresh(snapshot)

    gained_ids, lost_ids = calculate_changes(
        previous.id if previous else None,
        snapshot.id,
        db,
    )

    gained = []
    for pid in gained_ids:
        pl = db.query(Playlist).filter(Playlist.id == pid).first()
        pc = db.query(Placement).filter(
            Placement.playlist_id == pid,
            Placement.snapshot_id == snapshot.id,
        ).first()
        if pl and pc:
            gained.append(PlaylistSummary(
                id=pl.id,
                name=pl.name,
                playlist_type=_playlist_type_str(pl),
                tracks_count=pc.tracks_count,
            ))

    lost = []
    for pid in lost_ids:
        pl = db.query(Playlist).filter(Playlist.id == pid).first()
        if pl:
            lost.append(PlaylistSummary(
                id=pl.id,
                name=pl.name,
                playlist_type=_playlist_type_str(pl),
                tracks_count=0,
            ))

    current_placements = (
        db.query(Placement)
        .filter(Placement.artist_id == artist.id)
        .filter(Placement.snapshot_id == snapshot.id)
        .all()
    )
    current_playlists = _placements_to_summaries(current_placements, db)

    return ArtistQueryResponse(
        artist=artist,
        snapshot={
            "id": snapshot.id,
            "snapshot_time": snapshot.snapshot_time,
            "total_playlists_found": snapshot.total_playlists_found,
        },
        changes={"gained": gained, "lost": lost},
        current_playlists=current_playlists,
    )


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


@router.get("/{artist_id}/history", response_model=list[SnapshotWithChanges])
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
    result = []
    for i, s in enumerate(snapshots):
        prev_id = snapshots[i + 1].id if i + 1 < len(snapshots) else None
        gained_ids, lost_ids = calculate_changes(prev_id, s.id, db)
        result.append(
            SnapshotWithChanges(
                id=s.id,
                artist_id=s.artist_id,
                snapshot_time=s.snapshot_time,
                total_playlists_found=s.total_playlists_found,
                playlists_checked_count=s.playlists_checked_count,
                discovery_method_used=s.discovery_method_used,
                gained_count=len(gained_ids),
                lost_count=len(lost_ids),
            )
        )
    return result


@router.get("/{artist_id}/playlists", response_model=list[PlaylistSummary])
def get_artist_playlists(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )
    latest = (
        db.query(Snapshot)
        .filter(Snapshot.artist_id == artist_id)
        .order_by(Snapshot.snapshot_time.desc())
        .first()
    )
    if not latest:
        return []
    placements = (
        db.query(Placement)
        .filter(Placement.artist_id == artist_id)
        .filter(Placement.snapshot_id == latest.id)
        .all()
    )
    return _placements_to_summaries(placements, db)


@router.post("/{artist_id}/refresh", response_model=ArtistQueryResponse)
def refresh_artist(artist_id: int, db: Session = Depends(get_db)):
    artist = db.query(Artist).filter(Artist.id == artist_id).first()
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )
    return _run_discovery_and_respond(artist, db, update_name_from_spotify=True)


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
        current_playlists = _placements_to_summaries(current_placements, db)

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

    return _run_discovery_and_respond(artist, db, update_name_from_spotify=True)

