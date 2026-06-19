"""Preview JWT service tests."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force model registration
from husk.auth import models as _auth_models  # noqa: F401
from husk.core.database import Base
from husk.preview import models as _preview_models  # noqa: F401
from husk.preview.exceptions import PreviewTokenInvalid
from husk.preview.service import PreviewService
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


async def test_issue_and_verify_roundtrip(session) -> None:
    svc = PreviewService(session)
    pt, jwt_str = await svc.issue("sb_abc", port=8080)
    assert pt.sandbox_id == "sb_abc"
    assert pt.port == 8080
    assert jwt_str

    verified = await svc.verify(jwt_str)
    assert verified.id == pt.id
    assert verified.sandbox_id == "sb_abc"


async def test_verify_invalid_signature_rejected(session) -> None:
    svc = PreviewService(session)
    with pytest.raises(PreviewTokenInvalid):
        await svc.verify("not.a.valid.jwt")


async def test_verify_revoked_token_rejected(session) -> None:
    svc = PreviewService(session)
    pt, jwt_str = await svc.issue("sb_abc", port=8080)

    # Manually delete the row to simulate revocation
    await session.delete(pt)
    await session.commit()

    with pytest.raises(PreviewTokenInvalid):
        await svc.verify(jwt_str)
