"""Volume HTTP router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from husk.auth.dependencies import current_apikey

from .dependencies import volume_service
from .schemas import CreateVolumeRequest, VolumeResponse
from .service import VolumeService

router = APIRouter(dependencies=[Depends(current_apikey)])


@router.get("", response_model=list[VolumeResponse])
async def list_volumes(service: VolumeService = Depends(volume_service)) -> list[VolumeResponse]:
    return [VolumeResponse.model_validate(v) for v in await service.list()]


@router.post("", response_model=VolumeResponse, status_code=status.HTTP_201_CREATED)
async def create_volume(
    body: CreateVolumeRequest,
    service: VolumeService = Depends(volume_service),
) -> VolumeResponse:
    return VolumeResponse.model_validate(await service.create(body))


@router.get("/{volume_id}", response_model=VolumeResponse)
async def get_volume(
    volume_id: str,
    service: VolumeService = Depends(volume_service),
) -> VolumeResponse:
    return VolumeResponse.model_validate(await service.get(volume_id))


@router.delete("/{volume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_volume(
    volume_id: str,
    service: VolumeService = Depends(volume_service),
) -> None:
    await service.delete(volume_id)
