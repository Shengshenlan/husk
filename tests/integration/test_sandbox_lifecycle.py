"""End-to-end sandbox lifecycle test against a real Docker daemon.

Skipped unless the env var ``HUSK_INTEGRATION=1`` is set, because it requires:
  - A reachable Docker daemon (/var/run/docker.sock or DOCKER_HOST)
  - Network access to pull ``alpine`` (or whatever image the test names)
  - About 5–10 seconds of wall-clock per case

Run with:

    HUSK_INTEGRATION=1 uv run pytest tests/integration/ -v

This verifies the M1.1 milestone: real ``docker run`` + DB state machine.
"""

from __future__ import annotations

import os
import time

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import docker

# Ensure every domain's models are registered on Base.metadata
from husk.auth import models as _auth_models  # noqa: F401
from husk.core.database import Base
from husk.core.docker_client import DockerClient
from husk.preview import models as _preview_models  # noqa: F401
from husk.sandbox import models as _sandbox_models  # noqa: F401
from husk.sandbox.constants import SandboxState
from husk.sandbox.exceptions import SandboxNotFound
from husk.sandbox.schemas import CreateRequest
from husk.sandbox.service import SandboxService
from husk.snapshot import models as _snapshot_models  # noqa: F401
from husk.volume import models as _volume_models  # noqa: F401

pytestmark = pytest.mark.skipif(
    os.environ.get("HUSK_INTEGRATION") != "1",
    reason="Set HUSK_INTEGRATION=1 to run real-Docker tests",
)


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.fixture(scope="module")
def docker_real() -> DockerClient:
    return DockerClient(os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock"))


@pytest.fixture(autouse=True)
def cleanup_husk_containers() -> None:
    """Belt-and-braces: remove any leftover containers labelled husk=true after each test."""
    yield
    client = docker.DockerClient(
        base_url=os.environ.get("DOCKER_HOST", "unix:///var/run/docker.sock")
    )
    for c in client.containers.list(all=True, filters={"label": "husk=true"}):
        try:
            c.remove(force=True, v=True)
        except Exception:
            pass


async def test_create_runs_real_container(session, docker_real) -> None:
    svc = SandboxService(session, docker_real)
    sb = await svc.create(
        CreateRequest(
            name=f"itest-{int(time.time())}",
            snapshot_id="alpine:3.20",
            cpu=1,
            memory_mb=128,
        )
    )
    assert sb.state == SandboxState.STARTED
    assert sb.container_id, "container_id should be populated after create"

    # Verify the container actually exists and has our owner label.
    info = await docker_real.inspect(sb.container_id)
    assert info is not None, "container should exist in docker"
    assert info.state == "running"

    # Cleanup via service
    await svc.destroy(sb.id)
    with pytest.raises(SandboxNotFound):
        await svc.get(sb.id)
    assert await docker_real.inspect(sb.container_id) is None


async def test_stop_then_start_real_container(session, docker_real) -> None:
    svc = SandboxService(session, docker_real)
    sb = await svc.create(
        CreateRequest(name=f"itest-stop-{int(time.time())}", snapshot_id="alpine:3.20", cpu=1, memory_mb=128)
    )
    try:
        stopped = await svc.stop(sb.id)
        assert stopped.state == SandboxState.STOPPED

        info_after_stop = await docker_real.inspect(sb.container_id)
        assert info_after_stop is not None
        assert info_after_stop.state in {"exited", "stopped"}

        started = await svc.start(sb.id)
        assert started.state == SandboxState.STARTED

        info_after_start = await docker_real.inspect(sb.container_id)
        assert info_after_start is not None
        assert info_after_start.state == "running"
    finally:
        await svc.destroy(sb.id)


async def test_husk_label_visible_to_reaper(session, docker_real) -> None:
    """The reaper finds containers via the husk=true label filter."""
    svc = SandboxService(session, docker_real)
    sb = await svc.create(
        CreateRequest(name=f"itest-label-{int(time.time())}", snapshot_id="alpine:3.20", cpu=1, memory_mb=128)
    )
    try:
        listed = await docker_real.list_husk_containers()
        assert any(c.id == sb.container_id for c in listed), "labelled container should be visible"
    finally:
        await svc.destroy(sb.id)
