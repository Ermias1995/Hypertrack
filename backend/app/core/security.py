from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings


def get_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """
    erSimple API key authentication using X-API-Key head.
    """
    if settings.API_KEY and x_api_key == settings.API_KEY:
        return x_api_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )


ApiKeyDependency = Depends(get_api_key)

