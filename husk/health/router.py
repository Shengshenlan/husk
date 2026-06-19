"""HTTP router for the health domain. Endpoints will be implemented in M1."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/_placeholder")
async def _placeholder() -> dict[str, str]:
    return {"domain": "health", "status": "scaffolded"}
