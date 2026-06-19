"""Sandbox service — orchestrates the full lifecycle: docker + DB + daemon."""

from __future__ import annotations

import secrets

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.docker_client import DockerClient
from husk.core.time import utcnow

from . import schemas
from .constants import SandboxState
from .daemon_inject import inject_daemon
from .exceptions import (
    DuplicateSandboxName,
    SandboxCreateFailed,
    SandboxNotFound,
)
from .models import Sandbox
from .repository import SandboxRepository
from .state_machine import assert_can_transition

_DEFAULT_IMAGE = "python:3.12-slim"


def _generate_id() -> str:
    return f"sb_{secrets.token_hex(8)}"


def _generate_name() -> str:
    return f"sandbox-{secrets.token_hex(4)}"


class SandboxService:
    """All sandbox lifecycle logic. Called by router, CLI and scheduled tasks."""

    def __init__(self, db: AsyncSession, docker: DockerClient) -> None:
        self._db = db
        self._repo = SandboxRepository(db)
        self._docker = docker

    # ── reads ──

    async def list(self) -> list[Sandbox]:
        return await self._repo.list()

    async def get(self, sandbox_id: str) -> Sandbox:
        sb = await self._repo.get(sandbox_id)
        if sb is None:
            raise SandboxNotFound(f"sandbox {sandbox_id} not found")
        return sb

    # ── lifecycle ──

    async def create(self, req: schemas.CreateRequest) -> Sandbox:
        """Create a sandbox: insert (creating) → docker run → inject daemon → mark started.

        Rolls forward to ``error`` (with the container removed) on any failure.
        Snapshot resolution is minimal in M1.1: ``snapshot_id`` is taken as a
        literal image ref if no Snapshot row matches. Real lookup lands in M3.
        """
        name = req.name or _generate_name()
        if await self._repo.get_by_name(name):
            raise DuplicateSandboxName(f"sandbox '{name}' already exists")

        sandbox_id = _generate_id()
        sb = Sandbox(
            id=sandbox_id,
            name=name,
            snapshot_id=req.snapshot_id,
            state=SandboxState.CREATING,
            cpu=req.cpu,
            memory_mb=req.memory_mb,
            disk_gb=req.disk_gb,
            labels=req.labels,
            auto_stop_interval=req.auto_stop_interval,
            last_activity_at=utcnow(),
        )
        await self._repo.insert(sb)

        image = req.snapshot_id or _DEFAULT_IMAGE
        try:
            await self._docker.pull_image(image)
            info = await self._docker.run(
                image=image,
                sandbox_id=sandbox_id,
                sandbox_name=name,
                cpu=req.cpu,
                memory_mb=req.memory_mb,
                labels={f"husk.label.{k}": v for k, v in (req.labels or {}).items()},
            )
            sb.container_id = info.id
            await self._repo.save(sb)

            # Best-effort daemon injection — falls back gracefully when binary missing.
            await inject_daemon(self._docker, info.id, info.ip)

            sb.state = SandboxState.STARTED
            await self._repo.save(sb)
            logger.info("sandbox {} created and running (container={})", sandbox_id, info.id[:12])
            return sb
        except Exception as e:
            logger.exception("create failed for sandbox {}", sandbox_id)
            await self._mark_error_and_cleanup(sb)
            raise SandboxCreateFailed(str(e)) from e

    async def start(self, sandbox_id: str) -> Sandbox:
        sb = await self.get(sandbox_id)
        assert_can_transition(sb.state, SandboxState.STARTED)
        if sb.container_id is None:
            raise SandboxCreateFailed(f"sandbox {sandbox_id} has no container to start")

        await self._docker.start(sb.container_id)
        sb.state = SandboxState.STARTED
        sb.last_activity_at = utcnow()
        return await self._repo.save(sb)

    async def stop(self, sandbox_id: str) -> Sandbox:
        sb = await self.get(sandbox_id)
        assert_can_transition(sb.state, SandboxState.STOPPING)

        sb.state = SandboxState.STOPPING
        await self._repo.save(sb)

        if sb.container_id:
            await self._docker.stop(sb.container_id)
        sb.state = SandboxState.STOPPED
        return await self._repo.save(sb)

    async def destroy(self, sandbox_id: str) -> None:
        sb = await self.get(sandbox_id)
        assert_can_transition(sb.state, SandboxState.DESTROYING)

        sb.state = SandboxState.DESTROYING
        await self._repo.save(sb)

        if sb.container_id:
            await self._docker.remove(sb.container_id)
        await self._repo.delete(sb)
        logger.info("sandbox {} destroyed", sandbox_id)

    async def touch(self, sandbox_id: str) -> Sandbox:
        """Update ``last_activity_at`` to now (used by SDK to keep the sandbox alive)."""
        sb = await self.get(sandbox_id)
        sb.last_activity_at = utcnow()
        return await self._repo.save(sb)

    # ── internals ──

    async def _mark_error_and_cleanup(self, sb: Sandbox) -> None:
        sb.state = SandboxState.ERROR
        try:
            await self._repo.save(sb)
        except Exception:
            logger.exception("failed to write error state for sandbox {}", sb.id)
        if sb.container_id:
            try:
                await self._docker.remove(sb.container_id)
            except Exception:
                logger.exception("failed to clean up container {}", sb.container_id)
