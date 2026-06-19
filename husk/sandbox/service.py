"""Sandbox service — the orchestration heart of Husk."""

from __future__ import annotations

import secrets
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.docker_client import DockerClient

from . import schemas
from .constants import SandboxState
from .exceptions import DuplicateSandboxName, SandboxNotFound
from .models import Sandbox
from .repository import SandboxRepository


def _generate_id() -> str:
    return f"sb_{secrets.token_hex(8)}"


def _generate_name() -> str:
    return f"sandbox-{secrets.token_hex(4)}"


class SandboxService:
    def __init__(self, db: AsyncSession, docker: DockerClient) -> None:
        self._repo = SandboxRepository(db)
        self._docker = docker

    async def list(self) -> list[Sandbox]:
        return await self._repo.list()

    async def get(self, sandbox_id: str) -> Sandbox:
        sb = await self._repo.get(sandbox_id)
        if sb is None:
            raise SandboxNotFound(f"sandbox {sandbox_id} not found")
        return sb

    async def create(self, req: schemas.CreateRequest) -> Sandbox:
        name = req.name or _generate_name()
        if await self._repo.get_by_name(name):
            raise DuplicateSandboxName(f"sandbox '{name}' already exists")

        sb = Sandbox(
            id=_generate_id(),
            name=name,
            snapshot_id=req.snapshot_id,
            state=SandboxState.CREATING,
            cpu=req.cpu,
            memory_mb=req.memory_mb,
            disk_gb=req.disk_gb,
            labels=req.labels,
            auto_stop_interval=req.auto_stop_interval,
            last_activity_at=datetime.utcnow(),
        )
        await self._repo.insert(sb)
        # M1: docker run + inject_daemon() + wait_daemon_ready()
        # then update state=started + container_id
        return sb

    async def start(self, sandbox_id: str) -> Sandbox:
        raise NotImplementedError("Implemented in M1")

    async def stop(self, sandbox_id: str) -> Sandbox:
        raise NotImplementedError("Implemented in M1")

    async def destroy(self, sandbox_id: str) -> None:
        sb = await self.get(sandbox_id)
        # M1: docker rm -fv
        await self._repo.delete(sb)
