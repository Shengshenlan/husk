"""Smoke import test."""

from __future__ import annotations


def test_import_module() -> None:
    import langchain_husk

    assert langchain_husk is not None


def test_public_exports() -> None:
    from langchain_husk import HuskSandbox

    assert HuskSandbox is not None
