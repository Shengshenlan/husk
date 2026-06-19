"""Auto-stop: stop sandboxes whose ``last_activity_at`` exceeds their interval (M3)."""

from __future__ import annotations


async def tick() -> None:
    """One iteration of the auto-stop scheduler.

    M3:
      - SELECT * FROM sandbox WHERE state='started' AND auto_stop_interval IS NOT NULL
      - For each, if now() - last_activity_at > interval → call SandboxService.stop(id)
    """
    raise NotImplementedError("Implemented in M3")
