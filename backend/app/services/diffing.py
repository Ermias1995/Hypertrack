from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.placement import Placement
from app.models.snapshot import Snapshot


def get_playlist_ids_from_snapshot(snapshot_id: int, db: Session) -> set[int]:
    placements = (
        db.query(Placement)
        .filter(Placement.snapshot_id == snapshot_id)
        .all()
    )
    return {p.playlist_id for p in placements}


def calculate_changes(
    previous_snapshot_id: int | None,
    current_snapshot_id: int,
    db: Session,
) -> Tuple[List[int], List[int]]:
    if not previous_snapshot_id:
        return [], []
    
    previous_playlists = get_playlist_ids_from_snapshot(previous_snapshot_id, db)
    current_playlists = get_playlist_ids_from_snapshot(current_snapshot_id, db)
    
    gained = list(current_playlists - previous_playlists)
    lost = list(previous_playlists - current_playlists)
    
    return gained, lost
