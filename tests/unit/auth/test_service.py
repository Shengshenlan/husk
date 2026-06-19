"""ApiKey service unit tests."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force model registration on Base.metadata
from husk.auth import models as _auth_models  # noqa: F401
from husk.auth.exceptions import (
    ApiKeyNotFound,
    DuplicateApiKeyName,
    InvalidApiKey,
)
from husk.auth.service import ApiKeyService
from husk.core.database import Base
from husk.preview import models as _preview_models  # noqa: F401
from husk.sandbox import models as _sandbox_models  # noqa: F401
from husk.snapshot import models as _snapshot_models  # noqa: F401
from husk.volume import models as _volume_models  # noqa: F401


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as s:
        yield s
    await engine.dispose()


async def test_create_returns_plaintext_once(session) -> None:
    svc = ApiKeyService(session)
    row, plaintext = await svc.create("alpha")
    assert plaintext.startswith("hk_")
    assert len(plaintext) > 30
    assert row.prefix == plaintext[:12]
    # Hash should NOT equal plaintext
    assert row.key_hash != plaintext


async def test_duplicate_name_rejected(session) -> None:
    svc = ApiKeyService(session)
    await svc.create("dup")
    with pytest.raises(DuplicateApiKeyName):
        await svc.create("dup")


async def test_verify_correct_token(session) -> None:
    svc = ApiKeyService(session)
    _, plaintext = await svc.create("alpha")
    row = await svc.verify(plaintext)
    assert row.name == "alpha"
    assert row.last_used_at is not None


async def test_verify_wrong_token(session) -> None:
    svc = ApiKeyService(session)
    await svc.create("alpha")
    with pytest.raises(InvalidApiKey):
        await svc.verify("hk_thisIsNotARealToken________________________")


async def test_verify_missing_prefix(session) -> None:
    svc = ApiKeyService(session)
    with pytest.raises(InvalidApiKey):
        await svc.verify("not-a-husk-token")


async def test_revoke(session) -> None:
    svc = ApiKeyService(session)
    _, plaintext = await svc.create("alpha")
    await svc.revoke("alpha")
    with pytest.raises(InvalidApiKey):
        await svc.verify(plaintext)


async def test_revoke_missing(session) -> None:
    svc = ApiKeyService(session)
    with pytest.raises(ApiKeyNotFound):
        await svc.revoke("ghost")


async def test_ensure_root_generates_when_empty(session) -> None:
    svc = ApiKeyService(session)
    plaintext = await svc.ensure_root_key(None)
    assert plaintext is not None
    assert plaintext.startswith("hk_")
    # Calling again returns None (already has keys)
    assert await svc.ensure_root_key(None) is None


async def test_ensure_root_uses_configured(session) -> None:
    svc = ApiKeyService(session)
    fixed = "hk_a_pinned_root_key_xxxxxxxxxxxxxxxxxxxxxxxxx"
    out = await svc.ensure_root_key(fixed)
    assert out == fixed
    # Verify it's stored and verifiable
    row = await svc.verify(fixed)
    assert row.name == "root"
