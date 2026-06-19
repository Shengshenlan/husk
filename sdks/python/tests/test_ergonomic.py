"""Tests for husk_client.ergonomic — Husk and Sandbox high-level classes.

These tests use respx to mock the HTTP layer so they run without a real
Husk control plane. Real-server tests live in tests/integration/.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from husk_client import (
    DownloadResult,
    ExecuteResult,
    Husk,
    Sandbox,
    UploadResult,
)

_BASE = "http://test.local"
_KEY = "hk_test_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
_SBID = "sb_abc"


# ── Husk client ──


def test_husk_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HUSK_API_KEY", raising=False)
    with pytest.raises(ValueError, match="api_key"):
        Husk(base_url=_BASE)


def test_husk_picks_up_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HUSK_API_KEY", _KEY)
    h = Husk(base_url=_BASE)
    assert h._api_key == _KEY
    h.close()


@respx.mock
def test_husk_create_returns_sandbox_owning_lifecycle() -> None:
    h = Husk(base_url=_BASE, api_key=_KEY)
    respx.post(f"{_BASE}/api/sandbox").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "sb_new",
                "name": "test",
                "snapshot_id": "alpine:3.20",
                "state": "started",
                "cpu": 1,
                "memory_mb": 256,
                "disk_gb": 10,
                "labels": {},
                "runner_id": "default",
                "region": "default",
                "auto_stop_interval": None,
                "last_activity_at": None,
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            },
        )
    )
    sb = h.create(image="alpine:3.20")
    assert isinstance(sb, Sandbox)
    assert sb.id == "sb_new"
    assert sb._owns_lifecycle is True
    assert sb.state == "started"
    h.close()
    sb.close()


@respx.mock
def test_husk_get_does_not_own_lifecycle() -> None:
    h = Husk(base_url=_BASE, api_key=_KEY)
    respx.get(f"{_BASE}/api/sandbox/sb_existing").mock(
        return_value=httpx.Response(200, json={"id": "sb_existing", "state": "started"})
    )
    sb = h.get("sb_existing")
    assert sb.id == "sb_existing"
    assert sb._owns_lifecycle is False
    h.close()
    sb.close()


@respx.mock
def test_husk_list_returns_handles() -> None:
    h = Husk(base_url=_BASE, api_key=_KEY)
    respx.get(f"{_BASE}/api/sandbox").mock(
        return_value=httpx.Response(
            200,
            json=[
                {"id": "sb_1", "state": "started"},
                {"id": "sb_2", "state": "stopped"},
            ],
        )
    )
    sandboxes = h.list()
    assert [s.id for s in sandboxes] == ["sb_1", "sb_2"]
    assert all(s._owns_lifecycle is False for s in sandboxes)
    for s in sandboxes:
        s.close()
    h.close()


# ── Sandbox.process ──


def _make_sandbox() -> Sandbox:
    return Sandbox(
        base_url=_BASE,
        api_key=_KEY,
        sandbox_id=_SBID,
        owns_lifecycle=False,
    )


@respx.mock
def test_process_execute_returns_executeresult() -> None:
    sb = _make_sandbox()
    route = respx.post(f"{_BASE}/api/toolbox/{_SBID}/process/execute").mock(
        return_value=httpx.Response(
            200,
            json={"exit_code": 0, "stdout": "hi\n", "stderr": "", "result": "hi\n"},
        )
    )
    result = sb.process.execute("echo hi", timeout=10)
    assert isinstance(result, ExecuteResult)
    assert result.exit_code == 0
    assert result.stdout == "hi\n"
    assert result.result == "hi\n"  # alias

    body = json.loads(route.calls[0].request.content)
    assert body == {"command": "echo hi", "timeout": 10}
    sb.close()


@respx.mock
def test_process_code_run_python() -> None:
    sb = _make_sandbox()
    respx.post(f"{_BASE}/api/toolbox/{_SBID}/process/code-run").mock(
        return_value=httpx.Response(
            200, json={"exit_code": 0, "stdout": "3\n", "stderr": "", "result": "3\n"}
        )
    )
    result = sb.process.code_run("print(1+2)", language="python")
    assert result.stdout == "3\n"
    sb.close()


@respx.mock
def test_process_execute_passes_cwd_and_env() -> None:
    sb = _make_sandbox()
    route = respx.post(f"{_BASE}/api/toolbox/{_SBID}/process/execute").mock(
        return_value=httpx.Response(
            200, json={"exit_code": 0, "stdout": "", "stderr": ""}
        )
    )
    sb.process.execute("ls", cwd="/workspace", env={"FOO": "bar"})
    body = json.loads(route.calls[0].request.content)
    assert body["cwd"] == "/workspace"
    assert body["env"] == ["FOO=bar"]
    sb.close()


# ── Sandbox.fs ──


@respx.mock
def test_fs_list_parses_entries() -> None:
    sb = _make_sandbox()
    respx.get(f"{_BASE}/api/toolbox/{_SBID}/files").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "name": "x.txt",
                    "path": "/workspace/x.txt",
                    "is_dir": False,
                    "size": 5,
                    "mode": "-rw-r--r--",
                    "mod_time": "2026-01-01T00:00:00Z",
                }
            ],
        )
    )
    [f] = sb.fs.list("/workspace")
    assert f.name == "x.txt" and f.is_dir is False and f.size == 5
    sb.close()


@respx.mock
def test_fs_upload_files_returns_uploadresult() -> None:
    sb = _make_sandbox()
    respx.post(f"{_BASE}/api/toolbox/{_SBID}/files/folder").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.post(f"{_BASE}/api/toolbox/{_SBID}/files/upload").mock(
        return_value=httpx.Response(200, json={"path": "/tmp/x", "bytes": "5"})
    )
    [up] = sb.fs.upload_files([("/tmp/x", b"hello")])
    assert isinstance(up, UploadResult)
    assert up.error is None
    sb.close()


@respx.mock
def test_fs_upload_files_per_file_error_path() -> None:
    sb = _make_sandbox()
    respx.post(f"{_BASE}/api/toolbox/{_SBID}/files/folder").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.post(f"{_BASE}/api/toolbox/{_SBID}/files/upload").mock(
        return_value=httpx.Response(403, text="forbidden")
    )
    out = sb.fs.upload_files([("relative.txt", b"x"), ("/etc/ro", b"y")])
    assert out[0].error == "invalid_path"  # rejected client-side
    assert out[1].error == "http_403"  # surfaced from server
    sb.close()


@respx.mock
def test_fs_download_files_per_file_error_path() -> None:
    sb = _make_sandbox()

    def _route(request: httpx.Request) -> httpx.Response:
        path = request.url.params.get("path", "")
        if path == "/exists":
            return httpx.Response(200, content=b"data")
        if path == "/missing":
            return httpx.Response(404)
        return httpx.Response(500)

    respx.get(f"{_BASE}/api/toolbox/{_SBID}/files/download").mock(side_effect=_route)
    out = sb.fs.download_files(["relative", "/exists", "/missing"])
    assert out[0].error == "invalid_path"
    assert isinstance(out[1], DownloadResult)
    assert out[1].content == b"data" and out[1].error is None
    assert out[2].content is None and out[2].error == "file_not_found"
    sb.close()


# ── Sandbox lifecycle ──


@respx.mock
def test_sandbox_destroy_calls_control_plane() -> None:
    sb = _make_sandbox()
    route = respx.delete(f"{_BASE}/api/sandbox/{_SBID}").mock(
        return_value=httpx.Response(204)
    )
    sb.destroy()
    assert route.called
    sb.close()


@respx.mock
def test_sandbox_context_manager_destroys_when_owned() -> None:
    sb = Sandbox(base_url=_BASE, api_key=_KEY, sandbox_id=_SBID, owns_lifecycle=True)
    route = respx.delete(f"{_BASE}/api/sandbox/{_SBID}").mock(
        return_value=httpx.Response(204)
    )
    with sb:
        pass
    assert route.called


@respx.mock
def test_sandbox_context_manager_keeps_unowned() -> None:
    sb = Sandbox(base_url=_BASE, api_key=_KEY, sandbox_id=_SBID, owns_lifecycle=False)
    route = respx.delete(f"{_BASE}/api/sandbox/{_SBID}").mock(
        return_value=httpx.Response(204)
    )
    with sb:
        pass
    assert not route.called
