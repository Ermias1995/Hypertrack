from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False, index=True)
    snapshot_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    total_playlists_found = Column(Integer, default=0)
    playlists_checked_count = Column(Integer, default=0)
    discovery_method_used = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    artist = relationship("Artist", back_populates="snapshots")
    placements = relationship("Placement", back_populates="snapshot", cascade="all, delete-orphan")
