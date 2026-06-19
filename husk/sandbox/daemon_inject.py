"""Inject the Husk daemon binary into a freshly created sandbox container.

Phase 1: copies the embedded upstream Daytona daemon binary (AGPL) and
starts it. The daemon stays a separate process inside the container,
communicating with the control plane only over HTTP — see NOTICE for the
licensing rationale.

Real implementation lands in M1.
"""

from __future__ import annotations


async def inject_daemon(container_id: str) -> None:
    """Copy ``embedded/daemon-<arch>`` into the container at ``daemon_target`` and exec it.

    M1 will:
      1. tar the binary into a stream with put_archive(...)
      2. docker exec chmod +x
      3. docker exec -d daemon serve --port <port>
      4. wait until http://<container_ip>:<port>/version 200s
    """
    raise NotImplementedError("Implemented in M1")
