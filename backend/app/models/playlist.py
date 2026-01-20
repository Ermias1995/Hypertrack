from sqlalchemy import Column, Integer, String, DateTime, Enum, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
import enum


class PlaylistType(str, enum.Enum):
    EDITORIAL = "editorial"
    ALGORITHMIC = "algorithmic"
    USER_GENERATED = "user_generated"


class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    spotify_playlist_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    owner_id = Column(String, nullable=True)
    owner_name = Column(String, nullable=True)
    playlist_type = Column(Enum(PlaylistType), default=PlaylistType.USER_GENERATED)
    follower_count = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    placements = relationship("Placement", back_populates="playlist", cascade="all, delete-orphan")
