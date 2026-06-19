"""Common time helpers for Husk."""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return the current UTC time as a tz-aware datetime."""
    return datetime.now(UTC)
