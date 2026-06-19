"""Stub endpoints for upstream Daytona SDK compatibility.

The upstream SDKs (e.g. daytona-sdk-python) call /api/users/me, /api/organizations,
and /api/config on bootstrap. Husk is single-tenant, so these return
deterministic "default" values.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/users/me")
async def users_me() -> dict:
    return {
        "id": "user_default",
        "email": "user@husk.local",
        "name": "Husk User",
        "personalOrganizationId": "org_default",
    }


@router.get("/organizations")
async def organizations() -> list[dict]:
    return [
        {
            "id": "org_default",
            "name": "default",
            "personal": True,
            "role": "OWNER",
        }
    ]


@router.get("/config")
async def config() -> dict:
    return {
        "version": "husk",
        "sandboxRegions": [{"id": "default", "name": "default"}],
        "defaultRegion": "default",
    }
