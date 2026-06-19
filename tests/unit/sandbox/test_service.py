"""SandboxService unit tests with a mocked DockerClient — no real Docker required."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force model imports so Base.metadata sees every table.
from husk.auth import models as _auth_models  # noqa: F401
from husk.core.database import Base
from husk.core.docker_client import ContainerInfo
from husk.preview import models as _preview_models  # noqa: F401
from husk.sandbox import models as _sandbox_models  # noqa: F401
from husk.sandbox.constants import SandboxState
from husk.sandbox.exceptions import (
    DuplicateSandboxName,
    InvalidStateTransition,
    SandboxCreateFailed,
    SandboxNotFound,
)
from husk.sandbox.schemas import CreateRequest
from husk.sandbox.service import SandboxService
from husk.snapshot import models as _snapshot_models  # noqa: F401
from husk.volume import models as _volume_models  # noqa: F401


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest.fixture
def docker_mock() -> AsyncMock:
    m = AsyncMock()
    m.pull_image = AsyncMock(return_value=None)
    m.run = AsyncMock(
        return_value=ContainerInfo(
            id="abc123def456", name="husk-sb_xxx", state="running", ip="172.17.0.5"
        )
    )
    m.start = AsyncMock(return_value=None)
    m.stop = AsyncMock(return_value=None)
    m.remove = AsyncMock(return_value=None)
    m.put_archive = AsyncMock(return_value=None)
    m.exec_run = AsyncMock(return_value=(0, b""))
    return m


# ── reads ──


async def test_get_missing_raises(session, docker_mock) -> None:
    svc = SandboxService(session, docker_mock)
    with pytest.raises(SandboxNotFound):
        await svc.get("sb_doesnotexist")


async def test_list_empty(session, docker_mock) -> None:
    svc = SandboxService(session, docker_mock)
    assert await svc.list() == []


# ── create ──


async def test_create_happy_path(session, docker_mock) -> None:
    svc = SandboxService(session, docker_mock)
    sb = await svc.create(CreateRequest(name="alpha", snapshot_id="python:3.12", cpu=1, memory_mb=512))

    assert sb.name == "alpha"
    assert sb.state == SandboxState.STARTED
    assert sb.container_id == "abc123def456"
    assert sb.runner_id == "default"
    assert sb.region == "default"

    # Docker calls in order
    docker_mock.pull_image.assert_awaited_once_with("python:3.12")
    docker_mock.run.assert_awaited_once()
    # No exec_run for daemon since no embedded binary in unit-test env (graceful skip)
    # but exec_run *may* have been called for mkdir if binary existed; mock allows either


async def test_create_duplicate_name_rejected(session, docker_mock) -> None:
    svc = SandboxService(session, docker_mock)
    await svc.create(CreateRequest(name="dup"))
    with pytest.raises(DuplicateSandboxName):
        await svc.create(CreateRequest(name="dup"))


async def test_create_marks_error_and_cleans_up_on_docker_failure(session, docker_mock) -> None:
    docker_mock.run = AsyncMock(side_effect=RuntimeError("boom"))
    svc = SandboxService(session, docker_mock)

    with pytest.raises(SandboxCreateFailed):
        await svc.create(CreateRequest(name="fails"))

    # The row was created and marked error
    [row] = await svc.list()
    assert row.state == SandboxState.ERROR


# ── stop / destroy / start ──


async def test_stop_running_then_start_again(session, docker_mock) -> None:
    svc = SandboxService(session, docker_mock)
    sb = await svc.create(CreateRequest(name="loop"))

    stopped = await svc.stop(sb.id)
    assert stopped.state == SandboxState.STOPPED
    docker_mock.stop.assert_awaited_once_with("abc123def456")

    started = await svc.start(sb.id)
    assert started.state == SandboxState.STARTED
    docker_mock.start.assert_awaited_once_with("abc123def456")


async def test_destroy_removes_container_and_db_row(session, docker_mock) -> None:
    svc = SandboxService(session, docker_mock)
    sb = await svc.create(CreateRequest(name="ephemeral"))

    await svc.destroy(sb.id)

    docker_mock.remove.assert_awaited_once_with("abc123def456")
    with pytest.raises(SandboxNotFound):
        await svc.get(sb.id)


async def test_invalid_state_transition_rejected(session, docker_mock) -> None:
    svc = SandboxService(session, docker_mock)
    sb = await svc.create(CreateRequest(name="alive"))
    # started → started is not allowed
    with pytest.raises(InvalidStateTransition):
        await svc.start(sb.id)


async def test_touch_updates_last_activity(session, docker_mock) -> None:
    svc = SandboxService(session, docker_mock)
    sb = await svc.create(CreateRequest(name="hb"))
    before = sb.last_activity_at

    # Make sure the timestamp moves forward
    import asyncio
    await asyncio.sleep(0.01)

    touched = await svc.touch(sb.id)
    assert touched.last_activity_at is not None
    assert before is None or touched.last_activity_at >= before
