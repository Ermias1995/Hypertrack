from pydantic import BaseModel
from datetime import datetime


class SnapshotRead(BaseModel):
    id: int
    artist_id: int
    snapshot_time: datetime
    total_playlists_found: int
    playlists_checked_count: int
    discovery_method_used: str | None = None

    class Config:
        from_attributes = True


class SnapshotWithChanges(BaseModel):
    id: int
    artist_id: int
    snapshot_time: datetime
    total_playlists_found: int
    playlists_checked_count: int
    discovery_method_used: str | None = None
    gained_count: int = 0
    lost_count: int = 0

