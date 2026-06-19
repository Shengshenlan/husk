"""HTTP router for the toolbox domain. Endpoints will be implemented in M2."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/_placeholder")
async def _placeholder() -> dict[str, str]:
    return {"domain": "toolbox", "status": "scaffolded"}
