"""Integration tests against a real Husk control plane.

Skipped unless ``HUSK_INTEGRATION=1`` is set.

Required env:
    HUSK_BASE_URL   default http://localhost:8000
    HUSK_API_KEY    a valid API key on that server
    HUSK_IMAGE      sandbox image to use; default python:3.12-slim

Run with::

    HUSK_INTEGRATION=1 \\
      HUSK_BASE_URL=http://localhost:8790 \\
      HUSK_API_KEY=hk_... \\
      uv run pytest tests/integration_tests/ -v
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from husk_client import Husk, Sandbox

from langchain_husk import HuskSandbox

pytestmark = pytest.mark.skipif(
    os.environ.get("HUSK_INTEGRATION") != "1",
    reason="Set HUSK_INTEGRATION=1 to run real-Husk tests",
)


@pytest.fixture(scope="module")
def husk() -> Iterator[Husk]:
    h = Husk(
        base_url=os.environ.get("HUSK_BASE_URL", "http://localhost:8000"),
        api_key=os.environ["HUSK_API_KEY"],
    )
    try:
        yield h
    finally:
        h.close()


@pytest.fixture
def sandbox(husk: Husk) -> Iterator[Sandbox]:
    image = os.environ.get("HUSK_IMAGE", "python:3.12-slim")
    sb = husk.create(image=image, cpu=1, memory_mb=256)
    try:
        yield sb
    finally:
        sb.destroy()
        sb.close()


@pytest.fixture
def backend(sandbox: Sandbox) -> HuskSandbox:
    return HuskSandbox(sandbox=sandbox)


# ── identity ──


def test_id_round_trip(backend: HuskSandbox, sandbox: Sandbox) -> None:
    assert backend.id == sandbox.id
    assert backend.id.startswith("sb_")


# ── execute ──


def test_execute_returns_stdout(backend: HuskSandbox) -> None:
    result = backend.execute("echo hello world")
    assert result.exit_code == 0
    assert "hello world" in result.output


def test_execute_python_via_shell(backend: HuskSandbox) -> None:
    result = backend.execute("python3 -c 'print(1+2+3)'")
    assert result.exit_code == 0
    assert result.output.strip() == "6"


def test_execute_nonzero_exit_code(backend: HuskSandbox) -> None:
    result = backend.execute("exit 7")
    assert result.exit_code == 7


# ── files ──


def test_upload_then_download(backend: HuskSandbox) -> None:
    payload = b"langchain-husk integration test " + os.urandom(8)
    [up] = backend.upload_files([("/tmp/lh-itest.bin", payload)])
    assert up.error is None

    [down] = backend.download_files(["/tmp/lh-itest.bin"])
    assert down.error is None
    assert down.content == payload


def test_download_missing_file(backend: HuskSandbox) -> None:
    [resp] = backend.download_files(["/nope/does-not-exist"])
    assert resp.content is None
    assert resp.error == "file_not_found"


def test_upload_invalid_path(backend: HuskSandbox) -> None:
    [resp] = backend.upload_files([("relative.txt", b"x")])
    assert resp.error == "invalid_path"


# ── BaseSandbox-derived (uses execute + upload internally) ──


def test_basesandbox_methods_inherited(backend: HuskSandbox) -> None:
    """BaseSandbox composes ls/grep/glob/read/write/edit on top of our primitives.

    We don't exercise their full semantics here (BaseSandbox's own tests cover
    that); we just verify the methods are present so the integration is real.
    """
    for name in ("ls", "grep", "glob", "read", "write", "edit"):
        assert callable(getattr(backend, name))


# ── lifecycle is the SDK's job, not ours ──


def test_husk_sdk_owns_lifecycle(husk: Husk) -> None:
    """The SDK's context manager destroys; the partner does not."""
    with husk.create(image=os.environ.get("HUSK_IMAGE", "python:3.12-slim")) as sb:
        backend = HuskSandbox(sandbox=sb)
        assert backend.execute("true").exit_code == 0
        sb_id = sb.id
    listed_ids = {s.id for s in husk.list()}
    assert sb_id not in listed_ids
