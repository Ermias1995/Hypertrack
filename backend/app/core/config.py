from pydantic_settings import BaseSettings
from typing import List
import os

_DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]


class Settings(BaseSettings):
    API_KEY: str = "your-secret-api-key-change-in-production"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite:///./artist_tracker.db"

    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    
    # SoundCloud API Configuration
    SOUNDCLOUD_CLIENT_ID: str = ""
    SOUNDCLOUD_CLIENT_SECRET: str = ""
    
    # Music API Provider: "spotify", "soundcloud", or "mock"
    MUSIC_API_PROVIDER: str = "soundcloud"

    # Auth / JWT
    AUTH_SECRET_KEY: str = "change-me-to-a-long-random-string"
    AUTH_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        cors_str = os.getenv("CORS_ORIGINS", "").strip()
        if cors_str:
            # Normalize: strip trailing slashes so "https://x.com/" matches browser "https://x.com"
            origins = [
                origin.strip().rstrip("/")
                for origin in cors_str.split(",")
                if origin.strip()
            ]
            return origins if origins else _DEFAULT_CORS_ORIGINS
        return _DEFAULT_CORS_ORIGINS


settings = Settings()
