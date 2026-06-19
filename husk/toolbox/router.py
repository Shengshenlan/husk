"""Toolbox HTTP router — proxies /api/toolbox/{sandbox_id}/* to the daemon."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, WebSocket

from husk.auth.dependencies import current_apikey
from husk.core.deps import docker_client
from husk.core.docker_client import DockerClient
from husk.sandbox.dependencies import sandbox_service
from husk.sandbox.service import SandboxService

from .http_proxy import proxy_request
from .ws_proxy import proxy_websocket

router = APIRouter()


@router.api_route(
    "/{sandbox_id}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    dependencies=[Depends(current_apikey)],
)
async def toolbox_http(
    sandbox_id: str,
    path: str,
    request: Request,
    service: SandboxService = Depends(sandbox_service),
    docker: DockerClient = Depends(docker_client),
):
    sb = await service.get(sandbox_id)
    return await proxy_request(request, sb, docker, path)


@router.websocket("/{sandbox_id}/{path:path}")
async def toolbox_ws(
    sandbox_id: str,
    path: str,
    websocket: WebSocket,
    service: SandboxService = Depends(sandbox_service),
    docker: DockerClient = Depends(docker_client),
) -> None:
    sb = await service.get(sandbox_id)
    await proxy_websocket(websocket, sb, docker, path)
