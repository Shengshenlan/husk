"""Auth FastAPI dependencies."""

from __future__ import annotations

from fastapi import Depends, Header
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.config import settings
from husk.core.database import db_session

from .exceptions import InvalidApiKey
from .models import ApiKey
from .service import ApiKeyService


def apikey_service(db: AsyncSession = Depends(db_session)) -> ApiKeyService:
    return ApiKeyService(db)


async def current_apikey(
    authorization: str | None = Header(default=None),
    service: ApiKeyService = Depends(apikey_service),
) -> ApiKey:
    """Resolve the caller's ApiKey from ``Authorization: Bearer hk_...`` or session JWT."""
    if not authorization or not authorization.startswith("Bearer "):
        raise InvalidApiKey("Missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ").strip()

    if token.startswith("hk_"):
        return await service.verify(token)

    try:
        payload = jwt.decode(token, settings.preview_jwt_secret, algorithms=["HS256"])
        if payload.get("type") == "session":
            return ApiKey(
                id="session",
                name=payload.get("sub", "admin"),
                prefix="ss",
                key_hash="",
            )
    except Exception:
        pass

    raise InvalidApiKey("token not recognised")
