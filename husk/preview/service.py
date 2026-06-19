"""Preview URL service — JWT signing + verification for sandbox port access."""

from __future__ import annotations

import secrets
from datetime import timedelta

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.config import settings
from husk.core.time import utcnow

from .exceptions import PreviewTokenExpired, PreviewTokenInvalid
from .models import PreviewToken

_DEFAULT_TTL = timedelta(hours=1)
_ALG = "HS256"


class PreviewService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def issue(
        self,
        sandbox_id: str,
        port: int,
        ttl: timedelta = _DEFAULT_TTL,
    ) -> tuple[PreviewToken, str]:
        """Mint a signed JWT for ``(sandbox_id, port)`` and persist it.

        Returns ``(orm_row, jwt_string)``. The plaintext JWT IS the URL token.
        """
        token_id = f"pt_{secrets.token_hex(8)}"
        expires_at = utcnow() + ttl
        claims = {
            "tid": token_id,
            "sid": sandbox_id,
            "port": port,
            "exp": int(expires_at.timestamp()),
        }
        jwt_str = jwt.encode(claims, settings.preview_jwt_secret, algorithm=_ALG)
        row = PreviewToken(
            id=token_id,
            sandbox_id=sandbox_id,
            port=port,
            token=jwt_str,
            expires_at=expires_at,
        )
        self._db.add(row)
        await self._db.commit()
        await self._db.refresh(row)
        return row, jwt_str

    async def verify(self, token: str) -> PreviewToken:
        try:
            claims = jwt.decode(token, settings.preview_jwt_secret, algorithms=[_ALG])
        except JWTError as e:
            raise PreviewTokenInvalid(str(e)) from e

        # The DB row must still exist (not revoked).
        row = await self._db.execute(
            select(PreviewToken).where(PreviewToken.id == claims["tid"])
        )
        pt = row.scalar_one_or_none()
        if pt is None:
            raise PreviewTokenInvalid("token has been revoked")

        if pt.expires_at < utcnow().replace(tzinfo=None):
            raise PreviewTokenExpired("token expired")

        return pt
