"""Volume repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Volume


class VolumeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self) -> list[Volume]:
        result = await self._db.execute(select(Volume))
        return list(result.scalars().all())

    async def get(self, volume_id: str) -> Volume | None:
        return await self._db.get(Volume, volume_id)

    async def get_by_name(self, name: str) -> Volume | None:
        result = await self._db.execute(select(Volume).where(Volume.name == name))
        return result.scalar_one_or_none()

    async def insert(self, volume: Volume) -> Volume:
        self._db.add(volume)
        await self._db.commit()
        await self._db.refresh(volume)
        return volume

    async def delete(self, volume: Volume) -> None:
        await self._db.delete(volume)
        await self._db.commit()
