"""ApiKey service (M1 scaffold)."""

from __future__ import annotations

import secrets

from .repository import ApiKeyRepository


class ApiKeyService:
    def __init__(self, repo: ApiKeyRepository) -> None:
        self._repo = repo

    @staticmethod
    def generate_token() -> str:
        """Generate a fresh ``hk_<random>`` API key."""
        return f"hk_{secrets.token_urlsafe(32)}"
