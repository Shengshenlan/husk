"""Volume service — wraps Docker named volumes one-to-one."""

from __future__ import annotations

import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.docker_client import DockerClient

from . import schemas
from .exceptions import VolumeNotFound
from .models import Volume
from .repository import VolumeRepository


def _generate_id() -> str:
    return f"vl_{secrets.token_hex(8)}"


class VolumeService:
    def __init__(self, db: AsyncSession, docker: DockerClient) -> None:
        self._repo = VolumeRepository(db)
        self._docker = docker

    async def list(self) -> list[Volume]:
        return await self._repo.list()

    async def get(self, volume_id: str) -> Volume:
        v = await self._repo.get(volume_id)
        if v is None:
            raise VolumeNotFound(f"volume {volume_id} not found")
        return v

    async def create(self, req: schemas.CreateVolumeRequest) -> Volume:
        docker_name = f"husk-{req.name}"
        # Create the docker volume
        await self._docker.create_volume(docker_name)
        v = Volume(id=_generate_id(), name=req.name, docker_volume=docker_name)
        return await self._repo.insert(v)

    async def delete(self, volume_id: str) -> None:
        v = await self.get(volume_id)
        await self._docker.remove_volume(v.docker_volume)
        await self._repo.delete(v)
