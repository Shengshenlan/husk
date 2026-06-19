"""ApiKey repository (M1 scaffold — methods filled in M1 properly)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class ApiKeyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
