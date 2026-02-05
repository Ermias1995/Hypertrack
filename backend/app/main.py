from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.init_db import init_db
from app.api.routes import artists, playlists, config, auth
from app.core.security import ApiKeyDependency

app = FastAPI(
    title="Artist Playlist Placement Tracker API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    init_db()


app.include_router(
    auth.router,
    prefix="/api",
)

app.include_router(
    artists.router,
    prefix="/api",
    dependencies=[ApiKeyDependency],
)

app.include_router(
    playlists.router,
    prefix="/api",
    dependencies=[ApiKeyDependency],
)

app.include_router(
    config.router,
    prefix="/api",
    dependencies=[ApiKeyDependency],
)


@app.get("/")
async def root():
    return {"message": "Artist Playlist Placement Tracker API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
