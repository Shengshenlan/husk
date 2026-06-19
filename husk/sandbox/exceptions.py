"""Sandbox-domain exceptions."""

from husk.core.exceptions import Conflict, HuskError, NotFound


class SandboxNotFound(NotFound):
    code = "sandbox_not_found"


class DuplicateSandboxName(Conflict):
    code = "duplicate_sandbox_name"


class SandboxCreateFailed(HuskError):
    status_code = 500
    code = "sandbox_create_failed"


class InvalidStateTransition(HuskError):
    status_code = 409
    code = "invalid_state_transition"
