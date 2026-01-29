"""
Runtime music provider override.
Defaults to MUSIC_API_PROVIDER from settings; can be switched via API without restart.
"""

from typing import Optional

from app.core.config import settings

_provider_override: Optional[str] = None


def get_effective_provider() -> str:
    """Return the active music API provider: 'spotify', 'soundcloud', or 'mock'."""
    if _provider_override is not None:
        return _provider_override.strip().lower()
    return settings.MUSIC_API_PROVIDER.strip().lower()


def set_provider_override(provider: Optional[str]) -> None:
    """Set runtime provider override. Pass None to use env default again."""
    global _provider_override
    _provider_override = provider.strip().lower() if provider else None
