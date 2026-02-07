import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.init_db import init_db
from app.api.routes import artists, playlists, config, auth
from app.core.security import ApiKeyDependency

logger = logging.getLogger(__name__)

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
    expose_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Ensure unhandled exceptions return JSON with CORS headers (so browser gets a proper response)."""
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        raise exc
    logger.exception("Unhandled exception: %s", exc)
    origin = request.headers.get("origin", "")
    allowed = list(settings.CORS_ORIGINS)
    headers = {}
    if origin and origin in allowed:
        headers["Access-Control-Allow-Origin"] = origin
    elif allowed:
        headers["Access-Control-Allow-Origin"] = allowed[0]
    headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers,
    )


@app.on_event("startup")
async def startup_event():
    init_db()


app.include_router(
    auth.router,
    prefix="/api",
)

# Artists are per-user; requires JWT (no API key)
app.include_router(
    artists.router,
    prefix="/api",
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
