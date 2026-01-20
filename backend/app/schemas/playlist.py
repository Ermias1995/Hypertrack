from pydantic import BaseModel
from datetime import datetime


class PlaylistRead(BaseModel):
    id: int
    spotify_playlist_id: str
    name: str
    owner_id: str | None = None
    owner_name: str | None = None
    playlist_type: str
    follower_count: int | None = None
    created_at: datetime

    class Config:
        orm_mode = True
