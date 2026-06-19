"""Sandbox HTTP router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from husk.auth.dependencies import current_apikey

from .dependencies import sandbox_service
from .schemas import CreateRequest, SandboxResponse
from .service import SandboxService

router = APIRouter(dependencies=[Depends(current_apikey)])


@router.post(
    "",
    response_model=SandboxResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sandbox",
)
async def create_sandbox(
    body: CreateRequest,
    service: SandboxService = Depends(sandbox_service),
) -> SandboxResponse:
    sb = await service.create(body)
    return SandboxResponse.model_validate(sb)


@router.get("", response_model=list[SandboxResponse], summary="List all sandboxes")
async def list_sandboxes(
    service: SandboxService = Depends(sandbox_service),
) -> list[SandboxResponse]:
    return [SandboxResponse.model_validate(s) for s in await service.list()]


@router.get("/{sandbox_id}", response_model=SandboxResponse, summary="Get a sandbox by id")
async def get_sandbox(
    sandbox_id: str,
    service: SandboxService = Depends(sandbox_service),
) -> SandboxResponse:
    return SandboxResponse.model_validate(await service.get(sandbox_id))


@router.delete("/{sandbox_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Destroy a sandbox")
async def delete_sandbox(
    sandbox_id: str,
    service: SandboxService = Depends(sandbox_service),
) -> None:
    await service.destroy(sandbox_id)
