"""Snapshot HTTP router."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from husk.auth.dependencies import current_apikey

from .dependencies import snapshot_service
from .schemas import CreateSnapshotRequest, SnapshotResponse
from .service import SnapshotService

router = APIRouter(dependencies=[Depends(current_apikey)])


@router.post("", response_model=SnapshotResponse, status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    body: CreateSnapshotRequest,
    service: SnapshotService = Depends(snapshot_service),
) -> SnapshotResponse:
    snap = await service.create(body)
    return SnapshotResponse.model_validate(snap)


@router.get("", response_model=list[SnapshotResponse])
async def list_snapshots(
    service: SnapshotService = Depends(snapshot_service),
) -> list[SnapshotResponse]:
    return [SnapshotResponse.model_validate(s) for s in await service.list()]


@router.get("/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: str,
    service: SnapshotService = Depends(snapshot_service),
) -> SnapshotResponse:
    return SnapshotResponse.model_validate(await service.get(snapshot_id))
