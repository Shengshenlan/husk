"""Sandbox-domain constants and enums."""

from enum import StrEnum


class SandboxState(StrEnum):
    """Lifecycle states a sandbox can be in."""

    CREATING = "creating"
    STARTED = "started"
    STOPPING = "stopping"
    STOPPED = "stopped"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"
    ERROR = "error"


# Default resource caps when a CreateRequest omits them.
DEFAULT_CPU = 2
DEFAULT_MEMORY_MB = 2048
DEFAULT_DISK_GB = 10
