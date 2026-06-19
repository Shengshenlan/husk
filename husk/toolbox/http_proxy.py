"""Toolbox HTTP reverse proxy to the sandbox-internal daemon (M2 scaffold)."""

from __future__ import annotations


async def proxy_request(*args, **kwargs):
    """Forward an HTTP request from /api/toolbox/<id>/<path> to the daemon.

    M2:
      1. resolve sandbox_id → container IP via SandboxService
      2. httpx.AsyncClient stream forward (preserve method/headers/body)
      3. stream the response back without buffering
    """
    raise NotImplementedError("Implemented in M2")
