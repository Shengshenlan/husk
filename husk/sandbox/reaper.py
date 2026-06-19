"""Reaper: keep DB ↔ docker ps in sync. Runs at startup + periodically (M4)."""

from __future__ import annotations


async def reconcile() -> None:
    """Find orphans on either side and reconcile.

    M4:
      - For every Sandbox row with state=started but no live container → mark error
      - For every container labelled husk=true with no Sandbox row → remove
    """
    raise NotImplementedError("Implemented in M4")
