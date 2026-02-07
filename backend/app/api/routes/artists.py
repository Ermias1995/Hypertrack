from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.artist import Artist
from app.models.placement import Placement
from app.models.playlist import Playlist
from app.models.snapshot import Snapshot
from app.models.user import User
from app.schemas.artist import (
    ArtistCreate,
    ArtistCreateFromUrl,
    ArtistQueryRequest,
    ArtistQueryResponse,
    ArtistRead,
    PlaylistSummary,
)
from app.schemas.snapshot import SnapshotWithChanges
from app.services.diffing import calculate_changes
from app.services.discovery import discover_playlists, get_or_create_playlist
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
                total_tracks=getattr(p, "total_tracks", None),
            ))
    return out


def _run_discovery_and_respond(artist, db, update_name_from_spotify=True):
    spotify_id = artist.spotify_artist_id
    if update_name_from_spotify:
        try:
            data = get_spotify_artist(spotify_id)
            artist.name = data["name"]
            if data.get("image_url"):
                artist.image_url = data["image_url"]
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
    
    # Update artist timestamps - explicitly set to ensure they're updated
    now = datetime.now(timezone.utc)
    artist.last_snapshot_at = snapshot.snapshot_time
    artist.updated_at = now  # Explicitly set updated_at

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
            total_tracks=pl.get("total_tracks"),
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
                total_tracks=getattr(pc, "total_tracks", None),
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


@router.post(
    "/from-url",
    response_model=ArtistQueryResponse,
    summary="Create Artist from URL",
    description="Provide only the artist profile URL (SoundCloud or Spotify). The backend resolves the artist ID and name, creates the artist, and runs playlist discovery. Use this when working with SoundCloud or when you only have a URL.",
)
def create_artist_from_url(
    body: ArtistCreateFromUrl,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return query_artist(
        ArtistQueryRequest(spotify_url=body.url.strip(), force_refresh=False),
        db,
        current_user,
    )


@router.post(
    "/",
    response_model=ArtistRead,
    summary="Create Artist (advanced)",
    description="Manually provide provider ID, name, and URL. For SoundCloud: use SoundCloud user ID as spotify_artist_id and SoundCloud URL as spotify_url. Prefer POST /api/artists/from-url when you only have a URL.",
)
def create_artist(
    payload: ArtistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    artist = Artist(
        user_id=current_user.id,
        spotify_artist_id=payload.spotify_artist_id,
        name=payload.name,
        spotify_url=payload.spotify_url,
    )
    db.add(artist)
    db.commit()
    db.refresh(artist)
    return artist


@router.get("/", response_model=list[ArtistRead])
def list_artists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Artist).filter(Artist.user_id == current_user.id).all()


@router.get("/{artist_id}", response_model=ArtistRead)
def get_artist(
    artist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    artist = (
        db.query(Artist)
        .filter(Artist.id == artist_id, Artist.user_id == current_user.id)
        .first()
    )
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )
    return artist


@router.get("/{artist_id}/history", response_model=list[SnapshotWithChanges])
def get_artist_history(
    artist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    artist = (
        db.query(Artist)
        .filter(Artist.id == artist_id, Artist.user_id == current_user.id)
        .first()
    )
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


@router.get(
    "/{artist_id}/playlists",
    response_model=list[PlaylistSummary],
    summary="Get Artist Playlists",
    description="Returns playlists from the latest snapshot for this artist. The `artist_id` is the **internal database ID** (from `GET /api/artists/` or the `artist.id` in `POST /api/artists/query`), not the SoundCloud/Spotify artist ID.",
)
def get_artist_playlists(
    artist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    artist = (
        db.query(Artist)
        .filter(Artist.id == artist_id, Artist.user_id == current_user.id)
        .first()
    )
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artist with id {artist_id} not found. Use the internal DB id from GET /api/artists/ or from POST /api/artists/query.",
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
def refresh_artist(
    artist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    artist = (
        db.query(Artist)
        .filter(Artist.id == artist_id, Artist.user_id == current_user.id)
        .first()
    )
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )
    return _run_discovery_and_respond(artist, db, update_name_from_spotify=True)


@router.post("/query", response_model=ArtistQueryResponse)
def query_artist(
    payload: ArtistQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.core.provider import get_effective_provider
    from app.services.soundcloud_client import resolve_soundcloud_url

    url = payload.spotify_url.strip()

    # Detect provider and extract artist ID
    provider = get_effective_provider()
    artist_id = None

    # Check if it's a SoundCloud URL
    if "soundcloud.com" in url.lower() or "on.soundcloud.com" in url.lower():
        if provider == "soundcloud":
            # Resolve SoundCloud URL
            resolved = resolve_soundcloud_url(url)
            if resolved and resolved.get("kind") == "user":
                artist_id = resolved["id"]
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="SoundCloud URL must point to a user/artist profile",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SoundCloud URL provided but provider is not set to 'soundcloud'",
            )
    elif "spotify.com" in url.lower() or "open.spotify.com" in url.lower():
        # Spotify URL - extract ID from path
        artist_id = url.rstrip("/").split("/")[-1].split("?")[0]
    else:
        # Assume it's a direct ID (for backward compatibility)
        artist_id = url.rstrip("/").split("/")[-1].split("?")[0]

    if not (artist_id and str(artist_id).strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL: could not extract artist ID",
        )
    artist_id = str(artist_id).strip()

    artist = (
        db.query(Artist)
        .filter(
            Artist.spotify_artist_id == artist_id,
            Artist.user_id == current_user.id,
        )
        .first()
    )

    if artist and not payload.force_refresh:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Artist already in your list.",
        )

    try:
        spotify_artist_data = get_spotify_artist(artist_id)
        artist_name = spotify_artist_data["name"]
        artist_image_url = spotify_artist_data.get("image_url")
    except Exception:
        artist_name = artist_id
        artist_image_url = None

    if not artist:
        artist = Artist(
            user_id=current_user.id,
            spotify_artist_id=artist_id,
            name=artist_name,
            spotify_url=url,
            image_url=artist_image_url,
        )
        db.add(artist)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            db.expunge(artist)
            existing = db.query(Artist).filter(Artist.spotify_artist_id == artist_id).first()
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Artist already exists.",
                )
            if existing.user_id is None:
                existing.user_id = current_user.id
                existing.name = artist_name
                existing.spotify_url = url
                if artist_image_url:
                    existing.image_url = artist_image_url
                db.commit()
                db.refresh(existing)
                artist = existing
            elif existing.user_id == current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Artist already in your list.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Artist already tracked by another account.",
                )

    if payload.force_refresh:
        artist.name = artist_name
        artist.spotify_url = url
        if artist_image_url:
            artist.image_url = artist_image_url
        artist.updated_at = datetime.now(timezone.utc)  # Explicitly set updated_at on update

    try:
        return _run_discovery_and_respond(artist, db, update_name_from_spotify=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e) or "Music API credentials not configured",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch artist or discover playlists. Check provider credentials and URL.",
        )

