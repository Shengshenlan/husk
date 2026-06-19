"""Toolbox HTTP reverse proxy.

Forwards every ``/api/toolbox/{sandbox_id}/{...}`` request to the daemon
running inside the sandbox container at ``<container_ip>:<daemon_port>``.

The control plane never inspects the body — this is a pure transparent
forward that streams both directions.
"""

from __future__ import annotations

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from loguru import logger

from husk.core.config import settings
from husk.core.docker_client import DockerClient
from husk.sandbox.models import Sandbox

# Hop-by-hop headers per RFC 7230 §6.1 — must not be forwarded.
_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


async def _resolve_target(docker: DockerClient, sb: Sandbox) -> str:
    """Return ``http://<ip>:<port>`` for the sandbox's daemon."""
    if not sb.container_id:
        raise HTTPException(status_code=409, detail="sandbox has no running container")
    info = await docker.inspect(sb.container_id)
    if info is None:
        raise HTTPException(status_code=404, detail="container no longer exists")
    if info.ip is None:
        raise HTTPException(status_code=503, detail="container has no IP yet")
    return f"http://{info.ip}:{settings.daemon_port}"


async def proxy_request(
    request: Request,
    sb: Sandbox,
    docker: DockerClient,
    path: str,
) -> Response:
    """Forward an HTTP request to the daemon and stream the response back."""
    target = await _resolve_target(docker, sb)
    upstream_url = f"{target}/{path.lstrip('/')}"

    fwd_headers = {
        k: v for k, v in request.headers.items() if k.lower() not in _HOP_HEADERS
    }

    body = await request.body()

    client = httpx.AsyncClient(timeout=None)
    try:
        upstream_req = client.build_request(
            method=request.method,
            url=upstream_url,
            headers=fwd_headers,
            params=request.query_params,
            content=body,
        )
        upstream_resp = await client.send(upstream_req, stream=True)
    except httpx.ConnectError as e:
        await client.aclose()
        logger.warning("toolbox proxy connect failed: {} {}", upstream_url, e)
        raise HTTPException(status_code=502, detail="daemon unreachable") from e

    resp_headers = {
        k: v for k, v in upstream_resp.headers.items() if k.lower() not in _HOP_HEADERS
    }

    async def _stream():
        try:
            async for chunk in upstream_resp.aiter_raw():
                yield chunk
        finally:
            await upstream_resp.aclose()
            await client.aclose()

    return StreamingResponse(
        _stream(),
        status_code=upstream_resp.status_code,
        headers=resp_headers,
        media_type=upstream_resp.headers.get("content-type"),
    )
