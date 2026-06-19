"""Smoke test: import the FastAPI app and verify it starts."""

from fastapi.testclient import TestClient

from husk.main import app


def test_app_imports():
    assert app.title == "Husk"


def test_health_placeholder():
    with TestClient(app) as client:
        resp = client.get("/api/health/_placeholder")
        assert resp.status_code == 200
        assert resp.json() == {"domain": "health", "status": "scaffolded"}
