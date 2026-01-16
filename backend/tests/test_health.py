"""Tests for the health endpoint."""

from app.main import create_app
from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok() -> None:
    """Health check should return an OK status payload."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
