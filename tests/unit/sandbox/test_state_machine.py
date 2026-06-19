"""State machine unit tests — pure, no fixtures needed."""

import pytest

from husk.sandbox.constants import SandboxState
from husk.sandbox.exceptions import InvalidStateTransition
from husk.sandbox.state_machine import assert_can_transition


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("creating", SandboxState.STARTED),
        ("creating", SandboxState.ERROR),
        ("started", SandboxState.STOPPING),
        ("started", SandboxState.DESTROYING),
        ("stopping", SandboxState.STOPPED),
        ("stopped", SandboxState.STARTED),
        ("stopped", SandboxState.DESTROYING),
        ("destroying", SandboxState.DESTROYED),
        ("error", SandboxState.DESTROYING),
    ],
)
def test_allowed_transitions(current: str, target: SandboxState) -> None:
    assert_can_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("started", SandboxState.STARTED),  # idempotent transitions are NOT allowed
        ("stopped", SandboxState.STOPPING),  # must go via started
        ("destroyed", SandboxState.STARTED),  # destroyed is terminal
        ("error", SandboxState.STARTED),  # error → only destroying
        ("creating", SandboxState.STOPPING),  # creating must reach started first
    ],
)
def test_disallowed_transitions(current: str, target: SandboxState) -> None:
    with pytest.raises(InvalidStateTransition):
        assert_can_transition(current, target)


def test_unknown_state_rejected() -> None:
    with pytest.raises(InvalidStateTransition):
        assert_can_transition("not-a-state", SandboxState.STARTED)
