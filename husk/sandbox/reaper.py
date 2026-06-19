"""Reaper: keep DB ↔ docker ps in sync. Runs at startup + periodically."""

from __future__ import annotations

from loguru import logger
from sqlalchemy import select

from husk.core.docker_client import DockerClient

from .constants import SandboxState
from .models import Sandbox


async def reconcile(docker: DockerClient) -> dict[str, int]:
    """One reconciliation pass.

    Two phases:

      A. **Orphan containers** — labelled husk=true with no Sandbox row in
         the DB → remove from Docker (probably leftover from a crash).
      B. **Phantom sandboxes** — Sandbox row in 'started' state whose
         container has disappeared → mark state=error.

    Returns counts: ``{"orphans_removed": N, "phantoms_marked": M}``.
    """
    from husk.core import database as _db

    if _db.session_factory is None:
        return {"orphans_removed": 0, "phantoms_marked": 0}

    # Snapshot live containers + DB rows
    live = await docker.list_husk_containers()
    live_ids = {c.id for c in live}

    async with _db.session_factory() as session:
        result = await session.execute(select(Sandbox))
        db_rows = list(result.scalars().all())

    db_container_ids = {sb.container_id for sb in db_rows if sb.container_id}

    # Phase A: containers in Docker that DB doesn't know about
    orphans = [c for c in live if c.id not in db_container_ids]
    for orphan in orphans:
        try:
            await docker.remove(orphan.id)
            logger.info("reaper removed orphan container {}", orphan.id[:12])
        except Exception:
            logger.exception("reaper failed to remove {}", orphan.id)

    # Phase B: DB rows pointing at gone containers
    phantoms = [
        sb for sb in db_rows
        if sb.state == SandboxState.STARTED
        and sb.container_id
        and sb.container_id not in live_ids
    ]
    if phantoms:
        async with _db.session_factory() as session:
            for sb in phantoms:
                merged = await session.merge(sb)
                merged.state = SandboxState.ERROR
                logger.warning(
                    "reaper marked sandbox {} error (container {} vanished)",
                    sb.id,
                    sb.container_id[:12],
                )
            await session.commit()

    return {"orphans_removed": len(orphans), "phantoms_marked": len(phantoms)}
