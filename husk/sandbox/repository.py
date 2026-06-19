"""Sandbox repository — wraps SQLAlchemy queries for the Sandbox table."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Sandbox


class SandboxRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list(self) -> list[Sandbox]:
        result = await self._db.execute(select(Sandbox))
        return list(result.scalars().all())

    async def get(self, sandbox_id: str) -> Sandbox | None:
        return await self._db.get(Sandbox, sandbox_id)

    async def get_by_name(self, name: str) -> Sandbox | None:
        result = await self._db.execute(select(Sandbox).where(Sandbox.name == name))
        return result.scalar_one_or_none()

    async def insert(self, sandbox: Sandbox) -> Sandbox:
        self._db.add(sandbox)
        await self._db.commit()
        await self._db.refresh(sandbox)
        return sandbox

    async def save(self, sandbox: Sandbox) -> Sandbox:
        await self._db.commit()
        await self._db.refresh(sandbox)
        return sandbox

    async def delete(self, sandbox: Sandbox) -> None:
        await self._db.delete(sandbox)
        await self._db.commit()
