from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Placement(Base):
    __tablename__ = "placements"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False, index=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=False, index=True)
    tracks_count = Column(Integer, default=1)
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    artist = relationship("Artist", back_populates="placements")
    playlist = relationship("Playlist", back_populates="placements")
    snapshot = relationship("Snapshot", back_populates="placements")
