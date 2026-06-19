from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from husk.core.database import db_session
from husk.core.deps import docker_client
from husk.core.docker_client import DockerClient

from .service import VolumeService


def volume_service(
    db: AsyncSession = Depends(db_session),
    docker: DockerClient = Depends(docker_client),
) -> VolumeService:
    return VolumeService(db, docker)
