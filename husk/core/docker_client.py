"""Docker engine client wrapper. The ONLY place that talks to /var/run/docker.sock."""

from __future__ import annotations

import docker
from docker import DockerClient as _DockerSDKClient


class DockerClient:
    """Thin facade over docker-py. Concrete operations come in M1."""

    def __init__(self, host: str) -> None:
        self._client: _DockerSDKClient = docker.DockerClient(base_url=host)

    def ping(self) -> bool:
        """Return True iff the Docker daemon is reachable."""
        return bool(self._client.ping())

    @property
    def raw(self) -> _DockerSDKClient:
        """Escape hatch for code that needs the underlying docker-py client."""
        return self._client
