"""ApiKey service — generation, hashing, verification, persistence."""

from __future__ import annotations

import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.time import utcnow

from .exceptions import ApiKeyNotFound, DuplicateApiKeyName, InvalidApiKey
from .models import ApiKey

_ph = PasswordHasher()
_PREFIX = "hk_"


def generate_token() -> tuple[str, str, str]:
    """Generate a fresh ``hk_<random>`` API key.

    Returns ``(plaintext, prefix_for_display, argon2_hash)``.
    The plaintext is shown to the user exactly once and never persisted.
    """
    token = f"{_PREFIX}{secrets.token_urlsafe(32)}"
    prefix = token[:12]  # e.g. "hk_AbC123Xy"
    return token, prefix, _ph.hash(token)


class ApiKeyService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self) -> list[ApiKey]:
        result = await self._db.execute(select(ApiKey))
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> ApiKey | None:
        result = await self._db.execute(select(ApiKey).where(ApiKey.name == name))
        return result.scalar_one_or_none()

    async def create(self, name: str) -> tuple[ApiKey, str]:
        """Create a new API key. Returns ``(orm_row, plaintext)``.

        The plaintext token is returned exactly once; afterwards only the
        argon2 hash and prefix are kept.
        """
        if await self.get_by_name(name):
            raise DuplicateApiKeyName(f"api key '{name}' already exists")

        token, prefix, hashed = generate_token()
        row = ApiKey(
            id=f"ak_{secrets.token_hex(8)}",
            name=name,
            prefix=prefix,
            key_hash=hashed,
        )
        self._db.add(row)
        await self._db.commit()
        await self._db.refresh(row)
        return row, token

    async def revoke(self, name: str) -> None:
        row = await self.get_by_name(name)
        if row is None:
            raise ApiKeyNotFound(f"api key '{name}' not found")
        await self._db.delete(row)
        await self._db.commit()

    async def verify(self, token: str) -> ApiKey:
        """Validate a Bearer token. Raises InvalidApiKey on mismatch."""
        if not token or not token.startswith(_PREFIX):
            raise InvalidApiKey("token must be prefixed with hk_")

        prefix = token[:12]
        # Lookup by prefix narrows the candidate set; then argon2-verify each.
        result = await self._db.execute(
            select(ApiKey).where(ApiKey.prefix == prefix)
        )
        candidates = list(result.scalars().all())
        for row in candidates:
            try:
                _ph.verify(row.key_hash, token)
            except VerifyMismatchError:
                continue
            row.last_used_at = utcnow()
            await self._db.commit()
            return row

        raise InvalidApiKey("api key not recognised")

    async def ensure_root_key(self, configured_root: str | None) -> str | None:
        """Bootstrap the root API key on first start.

        - If ``configured_root`` is set, install/refresh it.
        - Else, if no keys exist at all, generate one and return its plaintext.
        - Else, return None (someone else already has keys).
        """
        existing = await self.list()
        if configured_root:
            # Install the configured key under the name "root" if not already there.
            existing_root = await self.get_by_name("root")
            if existing_root is None:
                row = ApiKey(
                    id=f"ak_{secrets.token_hex(8)}",
                    name="root",
                    prefix=configured_root[:12],
                    key_hash=_ph.hash(configured_root),
                )
                self._db.add(row)
                await self._db.commit()
            return configured_root

        if not existing:
            row, plaintext = await self.create("root")
            return plaintext

        return None
