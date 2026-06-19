"""Docker engine client wrapper. The ONLY place that talks to /var/run/docker.sock."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from docker.errors import APIError, ImageNotFound, NotFound
from docker.models.containers import Container
from loguru import logger

import docker
from docker import DockerClient as _DockerSDKClient

# Container label keys — used by the reaper to identify Husk-managed containers.
LABEL_OWNER = "husk"
LABEL_OWNER_VALUE = "true"
LABEL_SANDBOX_ID = "husk.sandbox.id"
LABEL_SANDBOX_NAME = "husk.sandbox.name"


@dataclass
class ContainerInfo:
    """Minimal container snapshot returned by ``DockerClient.run``/``inspect``."""

    id: str
    name: str
    state: str
    ip: str | None


def _container_info(c: Container) -> ContainerInfo:
    networks = (c.attrs or {}).get("NetworkSettings", {}).get("Networks", {})
    ip: str | None = None
    if networks:
        # First non-empty IPAddress wins (works for default bridge + custom networks).
        for net in networks.values():
            if net.get("IPAddress"):
                ip = net["IPAddress"]
                break
    return ContainerInfo(
        id=c.id or "",
        name=c.name or "",
        state=(c.attrs or {}).get("State", {}).get("Status", "unknown"),
        ip=ip,
    )


class DockerClient:
    """Thin async-friendly facade over docker-py."""

    def __init__(self, host: str) -> None:
        self._client: _DockerSDKClient = docker.DockerClient(base_url=host)

    # ── small helpers ──

    def ping(self) -> bool:
        return bool(self._client.ping())

    @property
    def raw(self) -> _DockerSDKClient:
        return self._client

    # ── lifecycle ──

    async def pull_image(self, image: str) -> None:
        """Pull ``image`` if not present locally. No-op when the tag is cached."""
        def _pull() -> None:
            try:
                self._client.images.get(image)
                return  # already cached
            except ImageNotFound:
                pass
            logger.info("pulling image {}", image)
            self._client.images.pull(image)

        await asyncio.to_thread(_pull)

    async def run(
        self,
        *,
        image: str,
        sandbox_id: str,
        sandbox_name: str,
        cpu: int,
        memory_mb: int,
        labels: dict[str, str] | None = None,
        env: dict[str, str] | None = None,
        command: list[str] | str | None = None,
    ) -> ContainerInfo:
        """Create + start a sandbox container, returning a fresh ContainerInfo."""

        merged_labels = {
            LABEL_OWNER: LABEL_OWNER_VALUE,
            LABEL_SANDBOX_ID: sandbox_id,
            LABEL_SANDBOX_NAME: sandbox_name,
            **(labels or {}),
        }

        def _run() -> Container:
            return self._client.containers.run(
                image=image,
                name=f"husk-{sandbox_id}",
                detach=True,
                labels=merged_labels,
                environment=env or {},
                command=command if command is not None else ["sleep", "infinity"],
                # Resources
                nano_cpus=int(cpu * 1_000_000_000),
                mem_limit=f"{memory_mb}m",
                # Hardening defaults (M1)
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                init=True,
                # Restart: Husk owns lifecycle, no automatic restart.
                restart_policy={"Name": "no"},
            )

        c: Container = await asyncio.to_thread(_run)
        await asyncio.to_thread(c.reload)  # refresh attrs to pick up the IP
        info = _container_info(c)
        logger.info("container created sandbox={} container={} ip={}", sandbox_id, c.short_id, info.ip)
        return info

    async def inspect(self, container_id: str) -> ContainerInfo | None:
        """Look up a container by id; return None if it no longer exists."""
        def _inspect() -> Container | None:
            try:
                c = self._client.containers.get(container_id)
                c.reload()
                return c
            except NotFound:
                return None

        c = await asyncio.to_thread(_inspect)
        return _container_info(c) if c is not None else None

    async def start(self, container_id: str) -> None:
        def _start() -> None:
            self._client.containers.get(container_id).start()
        await asyncio.to_thread(_start)

    async def stop(self, container_id: str, timeout: int = 10) -> None:
        def _stop() -> None:
            try:
                self._client.containers.get(container_id).stop(timeout=timeout)
            except NotFound:
                pass  # already gone — desired end state
        await asyncio.to_thread(_stop)

    async def remove(self, container_id: str) -> None:
        def _remove() -> None:
            try:
                self._client.containers.get(container_id).remove(force=True, v=True)
            except NotFound:
                pass
        await asyncio.to_thread(_remove)

    async def update(self, container_id: str, *, cpu: int, memory_mb: int) -> None:
        """Hot-resize a running container's CPU/memory limits."""
        def _update() -> None:
            self._client.containers.get(container_id).update(
                cpu_quota=cpu * 100_000,
                cpu_period=100_000,
                mem_limit=f"{memory_mb}m",
            )
        await asyncio.to_thread(_update)

    async def commit(self, container_id: str, repository: str) -> tuple[str, str]:
        """Run ``docker commit`` to create a new image from the container.

        Returns ``(image_id, image_ref)``.
        """
        def _commit() -> Any:
            container = self._client.containers.get(container_id)
            image = container.commit(repository=repository)
            return image

        image = await asyncio.to_thread(_commit)
        # docker-py returns Image; .id is "sha256:...", first tag is the human-readable ref
        tags = image.attrs.get("RepoTags") or [repository]
        return (image.id, tags[0])

    # ── volumes ──

    async def create_volume(self, name: str) -> None:
        def _create() -> None:
            self._client.volumes.create(name=name, labels={LABEL_OWNER: LABEL_OWNER_VALUE})
        await asyncio.to_thread(_create)

    async def remove_volume(self, name: str) -> None:
        def _remove() -> None:
            try:
                self._client.volumes.get(name).remove(force=True)
            except NotFound:
                pass
        await asyncio.to_thread(_remove)

    # ── exec / put_archive: needed by daemon_inject ──

    async def put_archive(self, container_id: str, path: str, tar_data: bytes) -> None:
        def _put() -> None:
            self._client.containers.get(container_id).put_archive(path, tar_data)
        await asyncio.to_thread(_put)

    async def exec_run(
        self,
        container_id: str,
        cmd: list[str] | str,
        *,
        detach: bool = False,
    ) -> tuple[int | None, bytes]:
        def _exec() -> Any:
            return self._client.containers.get(container_id).exec_run(cmd, detach=detach)

        result = await asyncio.to_thread(_exec)
        # detach=True returns ExecResult(exit_code=None, output=None)
        return (result.exit_code, result.output or b"")

    async def list_husk_containers(self) -> list[ContainerInfo]:
        """Used by the reaper: every container with our owner label."""
        def _list() -> list[Container]:
            return self._client.containers.list(
                all=True,
                filters={"label": f"{LABEL_OWNER}={LABEL_OWNER_VALUE}"},
            )

        try:
            cs = await asyncio.to_thread(_list)
        except APIError as e:
            logger.warning("failed to list husk containers: {}", e)
            return []
        return [_container_info(c) for c in cs]
