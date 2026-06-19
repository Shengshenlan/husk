"""Toolbox WebSocket reverse proxy (M2 scaffold)."""

from __future__ import annotations


async def pump(*args, **kwargs):
    """Two-way WebSocket pump between the browser/SDK and the daemon.

    Used for PTY streams, build-log tails, etc.

    M2: bidirectional asyncio task pair, cancel both on first close.
    """
    raise NotImplementedError("Implemented in M2")
