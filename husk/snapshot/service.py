"""Snapshot service (M3 scaffold)."""

from __future__ import annotations

import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.docker_client import DockerClient

from . import schemas
from .exceptions import SnapshotNotFound
from .models import Snapshot
from .repository import SnapshotRepository


class SnapshotService:
    def __init__(self, db: AsyncSession, docker: DockerClient) -> None:
        self._repo = SnapshotRepository(db)
        self._docker = docker

    async def list(self) -> list[Snapshot]:
        return await self._repo.list()

    async def get(self, snapshot_id: str) -> Snapshot:
        snap = await self._repo.get(snapshot_id)
        if snap is None:
            raise SnapshotNotFound(f"snapshot {snapshot_id} not found")
        return snap

    async def create(self, req: schemas.CreateSnapshotRequest) -> Snapshot:
        # M3: docker-py images.pull(req.image_ref) + measure size + state="active"
        snap = Snapshot(
            id=f"sn_{secrets.token_hex(8)}",
            name=req.name,
            image_ref=req.image_ref,
            state="pulling",
        )
        return await self._repo.insert(snap)

    async def get_or_pull(self, ref_or_id: str | None) -> Snapshot:
        """Used by SandboxService when creating a sandbox.

        M3 behavior:
          - if ref_or_id is a known snapshot id → return that
          - else treat it as an image_ref → pull on the fly
        """
        raise NotImplementedError("Implemented in M3")
