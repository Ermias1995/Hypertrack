from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.playlist import Playlist
from app.schemas.playlist import PlaylistRead


router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get("/{playlist_id}", response_model=PlaylistRead)
def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).first()
    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist not found",
        )
    return playlist
