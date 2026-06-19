"""Smoke test: verify the FastAPI app boots and core endpoints respond."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from husk.main import app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("smoke") / "husk.db"
    os.environ["HUSK_DB_URL"] = f"sqlite+aiosqlite:///{db_path}"
    # Pin a root key so the bootstrap is deterministic in tests.
    os.environ["HUSK_ROOT_API_KEY"] = "hk_smoke_test_root_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    with TestClient(app) as c:
        yield c


AUTH = {"Authorization": "Bearer hk_smoke_test_root_key_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"}


def test_app_imports() -> None:
    assert app.title == "Husk"


def test_health_returns_ok(client) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_stub_users_me(client) -> None:
    r = client.get("/api/users/me")
    assert r.status_code == 200
    assert r.json()["id"] == "user_default"


def test_stub_organizations(client) -> None:
    r = client.get("/api/organizations")
    assert r.status_code == 200 and len(r.json()) == 1


def test_sandbox_requires_auth(client) -> None:
    r = client.get("/api/sandbox")
    assert r.status_code == 401


def test_sandbox_with_bad_token_rejected(client) -> None:
    r = client.get("/api/sandbox", headers={"Authorization": "Bearer hk_obviously_wrong"})
    assert r.status_code == 401


def test_sandbox_with_root_token_accepted(client) -> None:
    r = client.get("/api/sandbox", headers=AUTH)
    assert r.status_code == 200
    assert r.json() == []


def test_openapi_schema_generates(client) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    for p in ("/api/sandbox", "/api/snapshots", "/api/health", "/api/api-keys"):
        assert p in paths


def test_create_revoke_apikey_via_api(client) -> None:
    # Create a child key
    r = client.post("/api/api-keys", headers=AUTH, json={"name": "child"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["key"].startswith("hk_") and len(body["key"]) > 30

    # New key works
    r = client.get("/api/sandbox", headers={"Authorization": f"Bearer {body['key']}"})
    assert r.status_code == 200

    # Revoke it
    r = client.delete("/api/api-keys/child", headers=AUTH)
    assert r.status_code == 204

    # Now it's rejected
    r = client.get("/api/sandbox", headers={"Authorization": f"Bearer {body['key']}"})
    assert r.status_code == 401
