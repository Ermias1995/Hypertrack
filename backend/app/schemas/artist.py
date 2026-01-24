from pydantic import BaseModel, Field


class ArtistCreateFromUrl(BaseModel):
    """Create an artist by providing only their profile URL. The backend resolves the provider (SoundCloud or Spotify) and fetches ID and name, then runs playlist discovery."""

    url: str = Field(..., description="Artist profile URL (e.g. https://soundcloud.com/artist-name or https://open.spotify.com/artist/...)")



class ArtistBase(BaseModel):
    spotify_artist_id: str = Field(..., description="Provider's artist ID (SoundCloud user ID when using SoundCloud, Spotify artist ID when using Spotify)")
    name: str
    spotify_url: str = Field(..., description="Provider profile URL (SoundCloud or Spotify artist URL)")


class ArtistCreate(ArtistBase):
    """Advanced: create an artist by manually providing ID, name, and URL. Prefer POST /api/artists/from-url with a single URL."""


class ArtistRead(ArtistBase):
    id: int

    class Config:
        from_attributes = True


class ArtistQueryRequest(BaseModel):
    spotify_url: str
    force_refresh: bool = False


class PlaylistSummary(BaseModel):
    id: int
    name: str
    playlist_type: str
    tracks_count: int

    class Config:
        from_attributes = True


class ArtistQueryResponse(BaseModel):
    artist: ArtistRead
    snapshot: dict
    changes: dict
    current_playlists: list[PlaylistSummary]

