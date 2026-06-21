"""Sandbox unit test fixtures — keep daemon injection mocked so no real HTTP probes fire."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_inject_daemon() -> AsyncMock:
    """Globally stub inject_daemon to prevent real daemon binary + HTTP probes."""
    with patch("husk.sandbox.service.inject_daemon", new_callable=AsyncMock) as m:
        m.return_value = True
        yield m
