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
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        cors_str = os.getenv("CORS_ORIGINS", "").strip()
        if cors_str:
            origins = [origin.strip() for origin in cors_str.split(",") if origin.strip()]
            return origins if origins else _DEFAULT_CORS_ORIGINS
        return _DEFAULT_CORS_ORIGINS


settings = Settings()
