"""Sandbox lifecycle state machine.

Visual:

    creating ──→ started ──→ stopping ──→ stopped
        │           │                          │
        │           └──→ destroying ←──────────┤
        │                    │                 │
        ↓                    ↓                 │
      error  ────────────→ destroyed           │
                             (then row deleted)│
                                               │
    stopped ──→ starting ──→ started  ─────────┘

Terminal states: ``destroyed`` (row removed), ``error`` (kept until manual cleanup).
"""

from __future__ import annotations

from .constants import SandboxState
from .exceptions import InvalidStateTransition

# Allowed transitions: from_state → set of valid to_states
_TRANSITIONS: dict[SandboxState, set[SandboxState]] = {
    SandboxState.CREATING: {SandboxState.STARTED, SandboxState.ERROR, SandboxState.DESTROYING},
    SandboxState.STARTED: {SandboxState.STOPPING, SandboxState.DESTROYING, SandboxState.ERROR},
    SandboxState.STOPPING: {SandboxState.STOPPED, SandboxState.ERROR},
    SandboxState.STOPPED: {SandboxState.STARTED, SandboxState.DESTROYING, SandboxState.ERROR},
    SandboxState.DESTROYING: {SandboxState.DESTROYED, SandboxState.ERROR},
    SandboxState.DESTROYED: set(),  # terminal
    SandboxState.ERROR: {SandboxState.DESTROYING},  # only escape is to destroy
}


def assert_can_transition(current: str, target: SandboxState) -> None:
    """Raise InvalidStateTransition if ``current → target`` is not allowed."""
    try:
        cur = SandboxState(current)
    except ValueError as e:
        raise InvalidStateTransition(f"unknown current state '{current}'") from e
    if target not in _TRANSITIONS.get(cur, set()):
        raise InvalidStateTransition(
            f"cannot transition {cur.value} → {target.value}"
        )
