.PHONY: format lint typecheck test integration_test help install

.DEFAULT_GOAL := help

UV_FROZEN ?= true

help:
	@echo "Targets:"
	@echo "  install         Install deps (test group)"
	@echo "  test            Run unit tests (no network)"
	@echo "  integration_test  Run tests against a real Husk; needs HUSK_API_KEY etc."
	@echo "  lint            ruff check"
	@echo "  format          ruff format + fix"

install:
	uv sync --group test

test:
	uv run --group test pytest -vv tests/test_import.py tests/unit_tests/

integration_test:
	uv run --group test pytest -vv tests/integration_tests/

lint:
	uv run ruff check langchain_husk tests

format:
	uv run ruff format langchain_husk tests
	uv run ruff check --fix langchain_husk tests

typecheck:
	@echo "(no typecheck wired yet — add ty/mypy here)"
