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
        orm_mode = True


class ArtistQueryRequest(BaseModel):
    spotify_url: str
    force_refresh: bool = False

