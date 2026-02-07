import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class RefreshTier(str, enum.Enum):
    DEFAULT = "default"
    TIER1 = "tier1"
    TIER2 = "tier2"


class Artist(Base):
    __tablename__ = "artists"
    __table_args__ = (UniqueConstraint("user_id", "spotify_artist_id", name="uq_artist_user_spotify_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    spotify_artist_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    spotify_url = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    refresh_tier = Column(Enum(RefreshTier), default=RefreshTier.DEFAULT)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_snapshot_at = Column(DateTime(timezone=True), nullable=True)

    snapshots = relationship("Snapshot", back_populates="artist", cascade="all, delete-orphan")
    placements = relationship("Placement", back_populates="artist", cascade="all, delete-orphan")
