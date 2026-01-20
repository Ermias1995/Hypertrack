from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.artist import Artist, Snapshot
from app.schemas.artist import ArtistCreate, ArtistRead, ArtistQueryRequest
from app.schemas.snapshot import SnapshotRead


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


@router.post("/query", response_model=ArtistRead)
def query_artist(payload: ArtistQueryRequest, db: Session = Depends(get_db)):
    url = payload.spotify_url.strip()
    spotify_id = url.rstrip("/").split("/")[-1].split("?")[0]

    artist = (
        db.query(Artist)
        .filter(Artist.spotify_artist_id == spotify_id)
        .first()
    )

    if artist and not payload.force_refresh:
        return artist

    if artist and payload.force_refresh:
        artist.spotify_url = url
    else:
        artist = Artist(
            spotify_artist_id=spotify_id,
            name=spotify_id,
            spotify_url=url,
        )
        db.add(artist)
        db.flush()

    snapshot = Snapshot(
        artist_id=artist.id,
        total_playlists_found=0,
        playlists_checked_count=0,
        discovery_method_used="initial",
    )
    db.add(snapshot)

    db.commit()
    db.refresh(artist)
    return artist

