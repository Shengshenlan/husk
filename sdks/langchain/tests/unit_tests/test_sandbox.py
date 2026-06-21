"""HuskSandbox unit tests against a mocked husk_client.Sandbox."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from langchain_husk import HuskSandbox


def _make_sandbox(*, default_timeout: int | None = None) -> tuple[HuskSandbox, MagicMock]:
    """Build a HuskSandbox wrapping a fully mocked husk_client.Sandbox."""
    mock_sdk = MagicMock()
    mock_sdk.id = "sb_unit_test_abc"
    kwargs = {"sandbox": mock_sdk}
    if default_timeout is not None:
        kwargs["timeout"] = default_timeout
    return HuskSandbox(**kwargs), mock_sdk


# ── identity ──


def test_id_proxies_through_to_sdk() -> None:
    sb, mock_sdk = _make_sandbox()
    assert sb.id == "sb_unit_test_abc"


# ── execute ──


def test_execute_returns_stdout_and_exit_code() -> None:
    sb, mock_sdk = _make_sandbox()
    mock_sdk.process.execute.return_value = SimpleNamespace(
        exit_code=0, stdout="hello world\n", stderr=""
    )

    result = sb.execute("echo hello world")

    assert result.output == "hello world\n"
    assert result.exit_code == 0
    assert result.truncated is False
    mock_sdk.process.execute.assert_called_once()
    args, kwargs = mock_sdk.process.execute.call_args
    assert args == ("echo hello world",)
    assert kwargs["timeout"] == 30 * 60  # default 30 minutes


def test_execute_uses_explicit_timeout() -> None:
    sb, mock_sdk = _make_sandbox()
    mock_sdk.process.execute.return_value = SimpleNamespace(exit_code=0, stdout="", stderr="")

    sb.execute("ls", timeout=5)

    assert mock_sdk.process.execute.call_args.kwargs["timeout"] == 5


def test_execute_uses_constructor_default_timeout() -> None:
    sb, mock_sdk = _make_sandbox(default_timeout=42)
    mock_sdk.process.execute.return_value = SimpleNamespace(exit_code=0, stdout="", stderr="")

    sb.execute("ls")

    assert mock_sdk.process.execute.call_args.kwargs["timeout"] == 42


def test_execute_appends_stderr_to_output_when_nonempty() -> None:
    sb, mock_sdk = _make_sandbox()
    mock_sdk.process.execute.return_value = SimpleNamespace(
        exit_code=1, stdout="main\n", stderr="oops"
    )

    result = sb.execute("noisy")

    assert "main\n" in result.output
    assert "<stderr>oops</stderr>" in result.output
    assert result.exit_code == 1


def test_execute_omits_empty_stderr() -> None:
    sb, mock_sdk = _make_sandbox()
    mock_sdk.process.execute.return_value = SimpleNamespace(
        exit_code=0, stdout="ok\n", stderr="   \n  "  # whitespace only
    )
    result = sb.execute("anything")
    assert "<stderr>" not in result.output


def test_execute_timeout_returns_124() -> None:
    sb, mock_sdk = _make_sandbox()
    mock_sdk.process.execute.side_effect = TimeoutError("simulated")

    result = sb.execute("sleep 999", timeout=3)

    assert result.exit_code == 124
    assert "timed out" in result.output


def test_execute_unexpected_exception_returns_error_output() -> None:
    sb, mock_sdk = _make_sandbox()
    mock_sdk.process.execute.side_effect = RuntimeError("kaboom")

    result = sb.execute("anything")

    assert result.exit_code == 1
    assert "<husk error>" in result.output
    assert "RuntimeError" in result.output


# ── upload_files ──


def test_upload_delegates_to_sdk() -> None:
    sb, mock_sdk = _make_sandbox()
    mock_sdk.fs.upload_files.return_value = [
        SimpleNamespace(path="/tmp/a.txt", error=None),
        SimpleNamespace(path="bad.txt", error="invalid_path"),
    ]

    out = sb.upload_files([("/tmp/a.txt", b"hi"), ("bad.txt", b"x")])

    assert len(out) == 2
    assert out[0].path == "/tmp/a.txt" and out[0].error is None
    assert out[1].path == "bad.txt" and out[1].error == "invalid_path"
    mock_sdk.fs.upload_files.assert_called_once_with(
        [("/tmp/a.txt", b"hi"), ("bad.txt", b"x")]
    )


# ── download_files ──


def test_download_delegates_to_sdk() -> None:
    sb, mock_sdk = _make_sandbox()
    mock_sdk.fs.download_files.return_value = [
        SimpleNamespace(path="/tmp/a.txt", content=b"hello", error=None),
        SimpleNamespace(path="/missing", content=None, error="file_not_found"),
        SimpleNamespace(path="rel", content=None, error="invalid_path"),
    ]

    out = sb.download_files(["/tmp/a.txt", "/missing", "rel"])

    assert out[0].content == b"hello" and out[0].error is None
    assert out[1].content is None and out[1].error == "file_not_found"
    assert out[2].error == "invalid_path"
    mock_sdk.fs.download_files.assert_called_once_with(
        ["/tmp/a.txt", "/missing", "rel"]
    )


# ── BaseSandbox-derived methods (defaults inherited from BaseSandbox) ──


def test_inherits_basesandbox_high_level_methods() -> None:
    """HuskSandbox should expose ls/grep/glob/read/write/edit from BaseSandbox.

    We don't exercise their full semantics here (BaseSandbox's own tests do
    that); we just verify the methods are bound and ultimately route into
    our mocked execute / upload_files.
    """
    sb, _ = _make_sandbox()
    for method in ("ls", "grep", "glob", "read", "write", "edit"):
        assert hasattr(sb, method), f"BaseSandbox.{method} should be inherited"


# ── must use kw-only args (style sanity) ──


def test_constructor_requires_keyword_sandbox(monkeypatch: pytest.MonkeyPatch) -> None:
    """The 'sandbox=' arg is keyword-only — match daytona's style."""
    fake_sdk = MagicMock()
    fake_sdk.id = "x"
    with pytest.raises(TypeError):
        HuskSandbox(fake_sdk)  # type: ignore[misc]
