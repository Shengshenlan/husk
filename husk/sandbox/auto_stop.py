"""Auto-stop: stop sandboxes whose ``last_activity_at`` exceeds their interval."""

from __future__ import annotations

from datetime import timedelta

from loguru import logger
from sqlalchemy import select

from husk.core.database import session_factory as _factory_var
from husk.core.docker_client import DockerClient
from husk.core.time import utcnow

from .constants import SandboxState
from .models import Sandbox
from .service import SandboxService


async def tick(docker: DockerClient) -> int:
    """One iteration of the auto-stop scheduler.

    Returns the number of sandboxes stopped this tick.
    """
    # Lazy access to the session factory (it's None until first init_db)
    from husk.core import database as _db

    if _db.session_factory is None:
        return 0

    stopped = 0
    now = utcnow().replace(tzinfo=None)

    async with _db.session_factory() as session:
        result = await session.execute(
            select(Sandbox).where(
                Sandbox.state == SandboxState.STARTED,
                Sandbox.auto_stop_interval.is_not(None),
                Sandbox.last_activity_at.is_not(None),
            )
        )
        candidates = list(result.scalars().all())

    if not candidates:
        return 0

    for sb in candidates:
        idle = now - sb.last_activity_at
        if idle < timedelta(seconds=sb.auto_stop_interval):
            continue

        async with _db.session_factory() as session:
            try:
                await SandboxService(session, docker).stop(sb.id)
                stopped += 1
                logger.info(
                    "auto-stopped sandbox {} (idle for {}s, threshold {}s)",
                    sb.id,
                    int(idle.total_seconds()),
                    sb.auto_stop_interval,
                )
            except Exception:
                logger.exception("auto-stop failed for sandbox {}", sb.id)

    return stopped


# Suppress unused-import warning (kept for backwards compat with old scheduler import)
_ = _factory_var
