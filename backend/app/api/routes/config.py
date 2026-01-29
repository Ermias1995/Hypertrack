"""Config API: get/set music provider (Spotify vs SoundCloud) at runtime."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.provider import get_effective_provider, set_provider_override

router = APIRouter(prefix="/config", tags=["config"])


class ConfigRead(BaseModel):
    provider: str = Field(..., description="Current music API provider: spotify or soundcloud")


class ConfigUpdate(BaseModel):
    provider: str = Field(..., description="Music API provider to use: spotify or soundcloud")


VALID_PROVIDERS = frozenset({"spotify", "soundcloud"})


@router.get("", response_model=ConfigRead)
def get_config():
    """Return current music provider."""
    return ConfigRead(provider=get_effective_provider())


@router.patch("", response_model=ConfigRead)
def update_config(payload: ConfigUpdate):
    """Switch music provider at runtime. Takes effect immediately for new requests."""
    raw = payload.provider.strip().lower()
    if raw not in VALID_PROVIDERS:
        raise HTTPException(
            status_code=422,
            detail=f"provider must be one of: {', '.join(sorted(VALID_PROVIDERS))}",
        )
    set_provider_override(raw)
    return ConfigRead(provider=get_effective_provider())
