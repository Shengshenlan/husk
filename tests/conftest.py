"""Global pytest fixtures shared across unit/integration/compat tests."""

import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"
