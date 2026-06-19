"""Preview router — issue/verify signed URLs + reverse-proxy /preview/{token}/*."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, Request

from husk.auth.dependencies import current_apikey
from husk.core.deps import docker_client
from husk.core.docker_client import DockerClient
from husk.sandbox.dependencies import sandbox_service
from husk.sandbox.service import SandboxService

from .dependencies import preview_service
from .proxy import proxy_to_port
from .schemas import IssuePreviewRequest, PreviewUrlResponse
from .service import PreviewService

router = APIRouter()


@router.post(
    "/issue",
    response_model=PreviewUrlResponse,
    dependencies=[Depends(current_apikey)],
    summary="Issue a signed preview URL for a sandbox port",
)
async def issue_preview_url(
    body: IssuePreviewRequest,
    request: Request,
    service: PreviewService = Depends(preview_service),
) -> PreviewUrlResponse:
    pt, jwt_str = await service.issue(
        sandbox_id=body.sandbox_id,
        port=body.port,
        ttl=timedelta(seconds=body.ttl_seconds),
    )
    base = str(request.base_url).rstrip("/")
    return PreviewUrlResponse(
        url=f"{base}/preview/{jwt_str}/",
        token=jwt_str,
        expires_at=pt.expires_at,
    )


@router.api_route(
    "/{token}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def preview_proxy(
    token: str,
    path: str,
    request: Request,
    service: PreviewService = Depends(preview_service),
    sandbox_svc: SandboxService = Depends(sandbox_service),
    docker: DockerClient = Depends(docker_client),
):
    return await proxy_to_port(request, token, path, service, sandbox_svc, docker)
