"""Preview port reverse proxy: /preview/{token}/{...} → http://<container_ip>:<port>/{...}"""

from __future__ import annotations

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from loguru import logger

from husk.core.docker_client import DockerClient
from husk.sandbox.service import SandboxService

from .exceptions import PreviewTokenExpired, PreviewTokenInvalid
from .service import PreviewService

_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}


async def proxy_to_port(
    request: Request,
    token: str,
    path: str,
    preview_service: PreviewService,
    sandbox_service: SandboxService,
    docker: DockerClient,
) -> Response:
    """Look up the token, locate the container, forward the HTTP request."""
    try:
        pt = await preview_service.verify(token)
    except PreviewTokenExpired as e:
        raise HTTPException(status_code=401, detail="preview token expired") from e
    except PreviewTokenInvalid as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    sb = await sandbox_service.get(pt.sandbox_id)
    if not sb.container_id:
        raise HTTPException(status_code=409, detail="sandbox not running")

    info = await docker.inspect(sb.container_id)
    if info is None or info.ip is None:
        raise HTTPException(status_code=404, detail="container/IP unavailable")

    target = f"http://{info.ip}:{pt.port}/{path.lstrip('/')}"
    fwd_headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP_HEADERS}
    body = await request.body()

    client = httpx.AsyncClient(timeout=None)
    try:
        upstream = await client.send(
            client.build_request(
                method=request.method,
                url=target,
                headers=fwd_headers,
                params=request.query_params,
                content=body,
            ),
            stream=True,
        )
    except httpx.ConnectError as e:
        await client.aclose()
        logger.warning("preview proxy connect failed: {} {}", target, e)
        raise HTTPException(status_code=502, detail="port unreachable") from e

    resp_headers = {k: v for k, v in upstream.headers.items() if k.lower() not in _HOP_HEADERS}

    async def _stream():
        try:
            async for chunk in upstream.aiter_raw():
                yield chunk
        finally:
            await upstream.aclose()
            await client.aclose()

    return StreamingResponse(
        _stream(),
        status_code=upstream.status_code,
        headers=resp_headers,
        media_type=upstream.headers.get("content-type"),
    )
