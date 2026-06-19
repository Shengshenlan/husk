"""Inject the Husk daemon binary into a freshly created sandbox container.

Phase 1: copies the embedded upstream Daytona daemon binary (AGPL) into
``/opt/husk/daemon`` and starts it. The daemon stays a separate process
inside the container, communicating with the control plane only over HTTP —
see NOTICE for the licensing rationale.

If the daemon binary doesn't exist on disk (e.g. local dev before the
``scripts/pull-upstream-daemon.sh`` script has been run), this is a no-op
that logs a warning. The sandbox is still functional for ``docker exec``-style
commands; only toolbox API access requires the daemon.
"""

from __future__ import annotations

import io
import os
import tarfile

import httpx
from loguru import logger

from husk.core.config import settings
from husk.core.docker_client import DockerClient


def _read_daemon_binary() -> bytes | None:
    """Read the embedded daemon binary, or None if not present."""
    if not os.path.exists(settings.daemon_bin):
        return None
    with open(settings.daemon_bin, "rb") as f:
        return f.read()


def _make_tar(name: str, data: bytes, mode: int = 0o755) -> bytes:
    """Pack a single file ``name`` (with mode) into a tar stream for ``put_archive``."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo(name=name)
        info.size = len(data)
        info.mode = mode
        tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


async def inject_daemon(docker: DockerClient, container_id: str, container_ip: str | None) -> bool:
    """Inject + start the daemon. Returns True on success, False if skipped/failed.

    Steps:
      1. Read embedded daemon binary.
      2. ``put_archive`` it into the container at ``/opt/husk/daemon`` (chmod 0755 via tar).
      3. ``exec -d`` the daemon process so it keeps running after the call returns.
      4. Probe the daemon's ``/version`` endpoint until it answers (or timeout).
    """
    binary = _read_daemon_binary()
    if binary is None:
        logger.warning(
            "daemon binary {} not found — skipping injection. "
            "Run scripts/pull-upstream-daemon.sh to embed it.",
            settings.daemon_bin,
        )
        return False

    # Strip the trailing filename so we put it into the parent directory.
    target_dir, target_filename = os.path.split(settings.daemon_target)
    await docker.exec_run(container_id, ["mkdir", "-p", target_dir])

    tar_blob = _make_tar(name=target_filename, data=binary)
    await docker.put_archive(container_id, target_dir, tar_blob)

    # Sanity-check chmod (tar mode usually wins, but belt-and-suspenders).
    await docker.exec_run(container_id, ["chmod", "+x", settings.daemon_target])

    # Start the daemon detached.
    await docker.exec_run(
        container_id,
        [settings.daemon_target, "serve", "--port", str(settings.daemon_port)],
        detach=True,
    )

    if container_ip is None:
        logger.warning("container {} has no IP — daemon readiness probe skipped", container_id)
        return True

    # Probe /version until ready or give up.
    if await _wait_daemon_ready(container_ip, settings.daemon_port):
        logger.info("daemon ready at http://{}:{}", container_ip, settings.daemon_port)
        return True

    logger.warning("daemon did not become ready within timeout for container {}", container_id)
    return False


async def _wait_daemon_ready(ip: str, port: int, *, attempts: int = 30, delay: float = 1.0) -> bool:
    url = f"http://{ip}:{port}/version"
    async with httpx.AsyncClient(timeout=2.0) as client:
        for _ in range(attempts):
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    return True
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError):
                pass
            import asyncio

            await asyncio.sleep(delay)
    return False
