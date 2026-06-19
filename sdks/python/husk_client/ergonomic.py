"""Ergonomic high-level API on top of the auto-generated husk-client.

The auto-generated client in ``husk_client._generated`` is endpoint-level
(``create_sandbox.sync(client=client, body=...)``). This module adds an
object-oriented façade that mirrors the upstream ``daytona-sdk-python``
shape, so SDK consumers can write::

    from husk_client import Husk

    husk = Husk(base_url="http://localhost:8000", api_key="hk_...")
    sandbox = husk.create(image="python:3.12-slim")
    print(sandbox.process.execute("python -c 'print(1+2)'").result)
    sandbox.fs.upload(path="/tmp/x.txt", content=b"hello")
    sandbox.destroy()

The toolbox proxy endpoints (``/api/toolbox/{id}/...``) are not enumerated
in the control plane's OpenAPI (they are pass-through), so this module
calls them directly with httpx instead of the generated client.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

_DEFAULT_HTTP_TIMEOUT = 60.0
_DEFAULT_IMAGE = "python:3.12-slim"


# ── result types ──


@dataclass
class ExecuteResult:
    """Outcome of a process/execute or process/code-run call."""

    exit_code: int
    stdout: str
    stderr: str = ""

    @property
    def result(self) -> str:
        """Alias of ``stdout`` matching the upstream SDK shape."""
        return self.stdout


@dataclass
class FileInfo:
    name: str
    path: str
    is_dir: bool
    size: int
    mode: str
    mod_time: str


@dataclass
class UploadResult:
    path: str
    error: str | None = None


@dataclass
class DownloadResult:
    path: str
    content: bytes | None
    error: str | None = None


# ── namespaces ──


class _ProcessNamespace:
    """Wraps ``/api/toolbox/{sandbox_id}/process/*``."""

    def __init__(self, sandbox: "Sandbox") -> None:
        self._sandbox = sandbox

    def execute(
        self,
        command: str,
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 0,
    ) -> ExecuteResult:
        """Run a shell command (``sh -c <command>``) synchronously."""
        body: dict[str, Any] = {"command": command, "timeout": timeout}
        if cwd:
            body["cwd"] = cwd
        if env:
            body["env"] = [f"{k}={v}" for k, v in env.items()]
        r = self._sandbox._toolbox_post("process/execute", json=body, timeout_s=timeout)
        data = r.json()
        return ExecuteResult(
            exit_code=int(data.get("exit_code", 0)),
            stdout=data.get("stdout", "") or data.get("result", "") or "",
            stderr=data.get("stderr", "") or "",
        )

    def code_run(
        self,
        code: str,
        *,
        language: str = "python",
        timeout: int = 0,
    ) -> ExecuteResult:
        """Run a code snippet (``python`` or ``bash``) synchronously."""
        body = {"code": code, "language": language, "timeout": timeout}
        r = self._sandbox._toolbox_post("process/code-run", json=body, timeout_s=timeout)
        data = r.json()
        return ExecuteResult(
            exit_code=int(data.get("exit_code", 0)),
            stdout=data.get("stdout", "") or data.get("result", "") or "",
            stderr=data.get("stderr", "") or "",
        )


class _FilesystemNamespace:
    """Wraps ``/api/toolbox/{sandbox_id}/files/*``."""

    def __init__(self, sandbox: "Sandbox") -> None:
        self._sandbox = sandbox

    def list(self, path: str = "/workspace") -> list[FileInfo]:
        r = self._sandbox._toolbox_get("files", params={"path": path})
        r.raise_for_status()
        return [FileInfo(**entry) for entry in r.json()]

    def info(self, path: str) -> FileInfo:
        r = self._sandbox._toolbox_get("files/info", params={"path": path})
        r.raise_for_status()
        return FileInfo(**r.json())

    def upload(self, *, path: str, content: bytes) -> None:
        """Upload one file. Raises on HTTP error."""
        # Best-effort mkdir for the parent directory.
        parent = os.path.dirname(path) or "/"
        self._sandbox._toolbox_post("files/folder", json={"path": parent})
        r = self._sandbox._toolbox.post(
            self._sandbox._toolbox_path("files/upload"),
            data={"path": path},
            files={"file": (os.path.basename(path) or "blob", content)},
        )
        r.raise_for_status()

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[UploadResult]:
        """Upload multiple files; per-file errors are returned, not raised."""
        out: list[UploadResult] = []
        for path, content in files:
            if not path.startswith("/"):
                out.append(UploadResult(path=path, error="invalid_path"))
                continue
            try:
                self.upload(path=path, content=content)
                out.append(UploadResult(path=path, error=None))
            except httpx.HTTPStatusError as e:
                out.append(UploadResult(path=path, error=f"http_{e.response.status_code}"))
            except Exception as e:  # noqa: BLE001
                out.append(UploadResult(path=path, error=str(e)))
        return out

    def download(self, path: str) -> bytes:
        """Download one file as bytes. Raises on HTTP error."""
        r = self._sandbox._toolbox_get("files/download", params={"path": path})
        r.raise_for_status()
        return r.content

    def download_files(self, paths: list[str]) -> list[DownloadResult]:
        """Download multiple files; per-file errors are returned, not raised."""
        out: list[DownloadResult] = []
        for path in paths:
            if not path.startswith("/"):
                out.append(DownloadResult(path=path, content=None, error="invalid_path"))
                continue
            try:
                r = self._sandbox._toolbox_get("files/download", params={"path": path})
                if r.status_code == 200:
                    out.append(DownloadResult(path=path, content=r.content, error=None))
                elif r.status_code == 404:
                    out.append(
                        DownloadResult(path=path, content=None, error="file_not_found")
                    )
                else:
                    out.append(
                        DownloadResult(
                            path=path, content=None, error=f"http_{r.status_code}"
                        )
                    )
            except Exception as e:  # noqa: BLE001
                out.append(DownloadResult(path=path, content=None, error=str(e)))
        return out

    def remove(self, path: str, *, recursive: bool = False) -> None:
        params = {"path": path}
        if recursive:
            params["recursive"] = "true"
        r = self._sandbox._toolbox.delete(
            self._sandbox._toolbox_path("files"), params=params
        )
        r.raise_for_status()

    def mkdir(self, path: str, *, mode: str | None = None) -> None:
        body: dict[str, Any] = {"path": path}
        if mode:
            body["mode"] = mode
        r = self._sandbox._toolbox_post("files/folder", json=body)
        r.raise_for_status()


# ── Sandbox handle ──


class Sandbox:
    """Ergonomic handle to a single Husk sandbox.

    Created by :meth:`Husk.create` or :meth:`Husk.get`. Don't instantiate
    directly unless you have a reason to.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        sandbox_id: str,
        owns_lifecycle: bool = False,
        http_timeout: float = _DEFAULT_HTTP_TIMEOUT,
        info: dict[str, Any] | None = None,
    ) -> None:
        self.id = sandbox_id
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._http_timeout = http_timeout
        self._owns_lifecycle = owns_lifecycle
        self._info = info or {}

        # Two clients on purpose: a short-timeout one for control-plane
        # lifecycle calls, and a no-default-timeout one for toolbox calls
        # (which carry their own command-level timeout).
        headers = {"Authorization": f"Bearer {api_key}"}
        self._control = httpx.Client(
            base_url=self._base_url, headers=headers, timeout=http_timeout
        )
        self._toolbox = httpx.Client(
            base_url=self._base_url, headers=headers, timeout=None
        )

        self.process = _ProcessNamespace(self)
        self.fs = _FilesystemNamespace(self)

    # ── Sandbox metadata ──

    @property
    def state(self) -> str:
        return str(self._info.get("state", "unknown"))

    @property
    def name(self) -> str:
        return str(self._info.get("name", self.id))

    def refresh(self) -> Sandbox:
        """Re-fetch this sandbox's metadata from the control plane."""
        r = self._control.get(f"/api/sandbox/{self.id}")
        r.raise_for_status()
        self._info = r.json()
        return self

    # ── lifecycle ──

    def start(self) -> Sandbox:
        r = self._control.post(f"/api/sandbox/{self.id}/start")
        r.raise_for_status()
        self._info = r.json()
        return self

    def stop(self) -> Sandbox:
        r = self._control.post(f"/api/sandbox/{self.id}/stop")
        r.raise_for_status()
        self._info = r.json()
        return self

    def destroy(self) -> None:
        try:
            self._control.delete(f"/api/sandbox/{self.id}")
        except httpx.HTTPError:
            pass

    # ── context manager ──

    def __enter__(self) -> Sandbox:
        return self

    def __exit__(self, *_exc: object) -> None:
        if self._owns_lifecycle:
            self.destroy()
        self.close()

    def close(self) -> None:
        self._control.close()
        self._toolbox.close()

    # ── internal helpers used by namespaces ──

    def _toolbox_path(self, suffix: str) -> str:
        return f"/api/toolbox/{self.id}/{suffix.lstrip('/')}"

    def _toolbox_get(self, suffix: str, **kwargs: Any) -> httpx.Response:
        return self._toolbox.get(self._toolbox_path(suffix), **kwargs)

    def _toolbox_post(
        self, suffix: str, *, json: Any = None, timeout_s: int | None = None, **kwargs: Any
    ) -> httpx.Response:
        # If the caller specifies a command timeout, leave generous HTTP slack on top.
        timeout = None if not timeout_s else float(timeout_s) + 30.0
        return self._toolbox.post(
            self._toolbox_path(suffix), json=json, timeout=timeout, **kwargs
        )


# ── Husk control-plane client ──


class Husk:
    """Ergonomic client for a Husk control plane.

    Use it to provision sandboxes::

        husk = Husk(base_url="http://localhost:8000", api_key="hk_...")
        sandbox = husk.create(image="python:3.12-slim")
        sandbox.process.execute("echo hi")
        sandbox.destroy()
    """

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8000",
        api_key: str | None = None,
        http_timeout: float = _DEFAULT_HTTP_TIMEOUT,
    ) -> None:
        resolved_key = api_key or os.environ.get("HUSK_API_KEY")
        if not resolved_key:
            raise ValueError(
                "api_key is required (pass directly or set HUSK_API_KEY env var)"
            )
        self._base_url = base_url.rstrip("/")
        self._api_key = resolved_key
        self._http_timeout = http_timeout
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {resolved_key}"},
            timeout=http_timeout,
        )

    # ── factories ──

    def create(
        self,
        *,
        name: str | None = None,
        image: str = _DEFAULT_IMAGE,
        cpu: int = 1,
        memory_mb: int = 512,
        labels: dict[str, str] | None = None,
        auto_stop_interval: int | None = None,
    ) -> Sandbox:
        """Provision a new sandbox; returns a Sandbox owning its own lifecycle."""
        body: dict[str, Any] = {
            "snapshot_id": image,
            "cpu": cpu,
            "memory_mb": memory_mb,
        }
        if name is not None:
            body["name"] = name
        if labels is not None:
            body["labels"] = labels
        if auto_stop_interval is not None:
            body["auto_stop_interval"] = auto_stop_interval

        r = self._client.post("/api/sandbox", json=body)
        r.raise_for_status()
        data = r.json()
        return Sandbox(
            base_url=self._base_url,
            api_key=self._api_key,
            sandbox_id=data["id"],
            owns_lifecycle=True,
            http_timeout=self._http_timeout,
            info=data,
        )

    def get(self, sandbox_id: str) -> Sandbox:
        """Return a Sandbox handle for an existing sandbox (no lifecycle ownership)."""
        r = self._client.get(f"/api/sandbox/{sandbox_id}")
        r.raise_for_status()
        return Sandbox(
            base_url=self._base_url,
            api_key=self._api_key,
            sandbox_id=sandbox_id,
            owns_lifecycle=False,
            http_timeout=self._http_timeout,
            info=r.json(),
        )

    def list(self) -> list[Sandbox]:
        """List all sandboxes; returned handles do NOT own lifecycle."""
        r = self._client.get("/api/sandbox")
        r.raise_for_status()
        return [
            Sandbox(
                base_url=self._base_url,
                api_key=self._api_key,
                sandbox_id=item["id"],
                owns_lifecycle=False,
                http_timeout=self._http_timeout,
                info=item,
            )
            for item in r.json()
        ]

    # ── context manager ──

    def __enter__(self) -> Husk:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()


# Used by ``Sandbox._info`` defaults; defined late to avoid forward refs.
_ = datetime  # silence unused-import warning if ``info["created_at"]`` work is added later
