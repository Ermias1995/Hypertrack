from pydantic import BaseModel


class ArtistBase(BaseModel):
    spotify_artist_id: str
    name: str
    spotify_url: str


class ArtistCreate(ArtistBase):
    pass


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

