"""Auth FastAPI dependencies (M1 scaffold)."""

from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.database import db_session

from .exceptions import InvalidApiKey


async def current_apikey(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(db_session),
):
    """Resolve the caller's ApiKey from the ``Authorization: Bearer hk_...`` header.

    Real verification (argon2 compare against stored hash) lands in M1.
    For the scaffold phase this only enforces "header present".
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise InvalidApiKey("Missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if not token.startswith("hk_"):
        raise InvalidApiKey("Token must be prefixed with hk_")
    return token  # placeholder: returns the raw token; M1 returns ApiKey ORM row
