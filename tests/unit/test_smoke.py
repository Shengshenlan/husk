"""Smoke test: verify the FastAPI app boots and core endpoints respond."""

from __future__ import annotations

from fastapi.testclient import TestClient

from husk.main import app


def test_app_imports() -> None:
    assert app.title == "Husk"


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "version" in body


def test_stub_users_me() -> None:
    with TestClient(app) as client:
        r = client.get("/api/users/me")
        assert r.status_code == 200
        assert r.json()["id"] == "user_default"


def test_stub_organizations() -> None:
    with TestClient(app) as client:
        r = client.get("/api/organizations")
        assert r.status_code == 200
        assert isinstance(r.json(), list) and len(r.json()) == 1


def test_sandbox_requires_auth() -> None:
    with TestClient(app) as client:
        r = client.get("/api/sandbox")
        assert r.status_code == 401


def test_sandbox_with_auth_returns_empty_list() -> None:
    with TestClient(app) as client:
        r = client.get("/api/sandbox", headers={"Authorization": "Bearer hk_test"})
        assert r.status_code == 200
        assert r.json() == []


def test_openapi_schema_generates() -> None:
    with TestClient(app) as client:
        r = client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert schema["info"]["title"] == "Husk"
        # All major domains should appear in the OpenAPI tags
        paths = schema["paths"]
        assert "/api/sandbox" in paths
        assert "/api/snapshots" in paths
        assert "/api/health" in paths
