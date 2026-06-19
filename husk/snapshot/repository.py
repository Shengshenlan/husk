"""Snapshot repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Snapshot


class SnapshotRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self) -> list[Snapshot]:
        result = await self._db.execute(select(Snapshot))
        return list(result.scalars().all())

    async def get(self, snapshot_id: str) -> Snapshot | None:
        return await self._db.get(Snapshot, snapshot_id)

    async def insert(self, snapshot: Snapshot) -> Snapshot:
        self._db.add(snapshot)
        await self._db.commit()
        await self._db.refresh(snapshot)
        return snapshot

    async def delete(self, snapshot: Snapshot) -> None:
        await self._db.delete(snapshot)
        await self._db.commit()
