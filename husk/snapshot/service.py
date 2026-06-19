"""Snapshot service — image-pull-based snapshots backed by Docker's image cache."""

from __future__ import annotations

import secrets

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.docker_client import DockerClient

from . import schemas
from .exceptions import SnapshotNotFound, SnapshotPullFailed
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

    async def get_by_image_ref(self, image_ref: str) -> Snapshot | None:
        return await self._repo.get_by_image_ref(image_ref)

    async def create(self, req: schemas.CreateSnapshotRequest) -> Snapshot:
        """Pull the image now, mark snapshot active. Errors mark it failed."""
        snap = Snapshot(
            id=f"sn_{secrets.token_hex(8)}",
            name=req.name,
            image_ref=req.image_ref,
            state="pulling",
        )
        await self._repo.insert(snap)
        try:
            await self._docker.pull_image(req.image_ref)
            snap.state = "active"
            await self._repo.save(snap)
            logger.info("snapshot {} pulled successfully ({})", snap.id, req.image_ref)
            return snap
        except Exception as e:
            logger.exception("snapshot {} pull failed", snap.id)
            snap.state = "failed"
            await self._repo.save(snap)
            raise SnapshotPullFailed(str(e)) from e

    async def delete(self, snapshot_id: str) -> None:
        snap = await self.get(snapshot_id)
        await self._repo.delete(snap)

    async def get_or_pull(self, ref_or_id: str | None) -> str:
        """Resolve a snapshot reference into a concrete image_ref.

        Order:
          1. If ``ref_or_id`` matches a Snapshot.id → return its image_ref
          2. If ``ref_or_id`` matches a Snapshot.image_ref → use it
          3. Else treat ``ref_or_id`` as a literal image ref and pull on demand
          4. None → caller picks a default
        """
        if ref_or_id is None:
            return "alpine:3.20"  # caller-friendly default

        # 1. id lookup
        snap = await self._repo.get(ref_or_id)
        if snap is not None and snap.state == "active":
            return snap.image_ref

        # 2. image_ref lookup
        existing = await self._repo.get_by_image_ref(ref_or_id)
        if existing is not None and existing.state == "active":
            return existing.image_ref

        # 3. on-the-fly pull
        await self._docker.pull_image(ref_or_id)
        return ref_or_id
