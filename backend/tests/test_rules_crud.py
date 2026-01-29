"""Tests for Rule CRUD endpoints with user scoping.

These endpoints allow authenticated users to manage their keyword-based
rules for article matching. All rules are scoped to the authenticated user.
"""

from __future__ import annotations

from collections.abc import Iterator

from app.core.settings import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def create_test_client() -> TestClient:
    """Create a TestClient with an isolated in-memory database."""
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    settings = Settings(
        app_name="Varthanam Test API",
        environment="test",
        log_level="INFO",
        database_url="sqlite+pysqlite://",
        jwt_secret_key="test-secret",
        jwt_access_token_expire_minutes=60,
    )
    app = create_app(settings=settings)

    def override_get_db_session() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    return TestClient(app)


def register_and_login(
    client: TestClient,
    email: str,
    password: str = "secure-password",
) -> str:
    """Register a user and return a bearer token."""
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    """Build authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {token}"}


# -----------------------------------------------------------------------------
# Create Rule Tests
# -----------------------------------------------------------------------------


def test_create_rule_minimal() -> None:
    """Authenticated users can create a rule with required fields only."""
    client = create_test_client()
    token = register_and_login(client, "create@example.com")

    response = client.post(
        "/api/v1/rules",
        json={"name": "Tech News", "frequency_minutes": 60},
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Tech News"
    assert payload["frequency_minutes"] == 60
    assert payload["is_active"] is True
    assert payload["include_keywords"] is None
    assert payload["exclude_keywords"] is None
    assert payload["collection_id"] is None
    assert "id" in payload
    assert "created_at" in payload
    assert "updated_at" in payload


def test_create_rule_with_all_fields() -> None:
    """Authenticated users can create a rule with all optional fields."""
    client = create_test_client()
    token = register_and_login(client, "full@example.com")

    # First create a collection
    col_response = client.post(
        "/api/v1/collections",
        json={"name": "Tech"},
        headers=auth_headers(token),
    )
    collection_id = col_response.json()["id"]

    response = client.post(
        "/api/v1/rules",
        json={
            "name": "AI Research",
            "frequency_minutes": 30,
            "include_keywords": "machine learning,neural network",
            "exclude_keywords": "crypto,bitcoin",
            "collection_id": collection_id,
            "is_active": False,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "AI Research"
    assert payload["frequency_minutes"] == 30
    assert payload["include_keywords"] == "machine learning,neural network"
    assert payload["exclude_keywords"] == "crypto,bitcoin"
    assert payload["collection_id"] == collection_id
    assert payload["is_active"] is False


def test_create_rule_requires_name() -> None:
    """Rule name is required."""
    client = create_test_client()
    token = register_and_login(client, "noname@example.com")

    response = client.post(
        "/api/v1/rules",
        json={"frequency_minutes": 60},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_create_rule_requires_frequency_minutes() -> None:
    """Rule frequency_minutes is required."""
    client = create_test_client()
    token = register_and_login(client, "nofreq@example.com")

    response = client.post(
        "/api/v1/rules",
        json={"name": "Missing Frequency"},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_create_rule_frequency_must_be_positive() -> None:
    """Rule frequency_minutes must be > 0."""
    client = create_test_client()
    token = register_and_login(client, "zerofreq@example.com")

    response = client.post(
        "/api/v1/rules",
        json={"name": "Zero Frequency", "frequency_minutes": 0},
        headers=auth_headers(token),
    )

    assert response.status_code == 422

    response = client.post(
        "/api/v1/rules",
        json={"name": "Negative Frequency", "frequency_minutes": -1},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_create_rule_keywords_must_be_nonempty_if_provided() -> None:
    """Keywords must be non-empty strings if provided."""
    client = create_test_client()
    token = register_and_login(client, "emptykw@example.com")

    response = client.post(
        "/api/v1/rules",
        json={
            "name": "Empty Keywords",
            "frequency_minutes": 60,
            "include_keywords": "",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_create_rule_requires_authentication() -> None:
    """Creating a rule requires authentication."""
    client = create_test_client()

    response = client.post(
        "/api/v1/rules",
        json={"name": "Unauthenticated", "frequency_minutes": 60},
    )

    assert response.status_code == 401


# -----------------------------------------------------------------------------
# List Rules Tests
# -----------------------------------------------------------------------------


def test_list_rules_returns_own_rules() -> None:
    """Users can list their own rules."""
    client = create_test_client()
    token = register_and_login(client, "list@example.com")

    # Create two rules
    client.post(
        "/api/v1/rules",
        json={"name": "Rule 1", "frequency_minutes": 60},
        headers=auth_headers(token),
    )
    client.post(
        "/api/v1/rules",
        json={"name": "Rule 2", "frequency_minutes": 30},
        headers=auth_headers(token),
    )

    response = client.get("/api/v1/rules", headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    names = [r["name"] for r in payload]
    assert "Rule 1" in names
    assert "Rule 2" in names


def test_list_rules_excludes_other_users_rules() -> None:
    """Users cannot see other users' rules."""
    client = create_test_client()
    token_a = register_and_login(client, "user-a@example.com")
    token_b = register_and_login(client, "user-b@example.com")

    # User A creates a rule
    client.post(
        "/api/v1/rules",
        json={"name": "User A Rule", "frequency_minutes": 60},
        headers=auth_headers(token_a),
    )

    # User B creates a rule
    client.post(
        "/api/v1/rules",
        json={"name": "User B Rule", "frequency_minutes": 30},
        headers=auth_headers(token_b),
    )

    # User A only sees their own rule
    response_a = client.get("/api/v1/rules", headers=auth_headers(token_a))
    assert response_a.status_code == 200
    payload_a = response_a.json()
    assert len(payload_a) == 1
    assert payload_a[0]["name"] == "User A Rule"

    # User B only sees their own rule
    response_b = client.get("/api/v1/rules", headers=auth_headers(token_b))
    assert response_b.status_code == 200
    payload_b = response_b.json()
    assert len(payload_b) == 1
    assert payload_b[0]["name"] == "User B Rule"


def test_list_rules_empty() -> None:
    """Users with no rules get an empty list."""
    client = create_test_client()
    token = register_and_login(client, "empty@example.com")

    response = client.get("/api/v1/rules", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json() == []


# -----------------------------------------------------------------------------
# Get Single Rule Tests
# -----------------------------------------------------------------------------


def test_get_rule_by_id() -> None:
    """Users can retrieve a single rule by ID."""
    client = create_test_client()
    token = register_and_login(client, "get@example.com")

    create_response = client.post(
        "/api/v1/rules",
        json={"name": "Get Me", "frequency_minutes": 60},
        headers=auth_headers(token),
    )
    rule_id = create_response.json()["id"]

    response = client.get(f"/api/v1/rules/{rule_id}", headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == rule_id
    assert payload["name"] == "Get Me"


def test_get_rule_not_found() -> None:
    """Getting a non-existent rule returns 404."""
    client = create_test_client()
    token = register_and_login(client, "notfound@example.com")

    response = client.get("/api/v1/rules/99999", headers=auth_headers(token))

    assert response.status_code == 404


def test_get_rule_access_control() -> None:
    """Users cannot access other users' rules."""
    client = create_test_client()
    token_a = register_and_login(client, "owner@example.com")
    token_b = register_and_login(client, "intruder@example.com")

    # User A creates a rule
    create_response = client.post(
        "/api/v1/rules",
        json={"name": "Private Rule", "frequency_minutes": 60},
        headers=auth_headers(token_a),
    )
    rule_id = create_response.json()["id"]

    # User B tries to access User A's rule
    response = client.get(f"/api/v1/rules/{rule_id}", headers=auth_headers(token_b))

    # Should return 404 (not 403) to avoid leaking existence
    assert response.status_code == 404


# -----------------------------------------------------------------------------
# Update Rule Tests
# -----------------------------------------------------------------------------


def test_update_rule_partial() -> None:
    """Users can partially update their rules."""
    client = create_test_client()
    token = register_and_login(client, "update@example.com")

    create_response = client.post(
        "/api/v1/rules",
        json={"name": "Original Name", "frequency_minutes": 60},
        headers=auth_headers(token),
    )
    rule_id = create_response.json()["id"]

    # Update only the name
    response = client.patch(
        f"/api/v1/rules/{rule_id}",
        json={"name": "Updated Name"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Updated Name"
    assert payload["frequency_minutes"] == 60  # Unchanged


def test_update_rule_all_fields() -> None:
    """Users can update multiple fields at once."""
    client = create_test_client()
    token = register_and_login(client, "fullupdate@example.com")

    create_response = client.post(
        "/api/v1/rules",
        json={"name": "Original", "frequency_minutes": 60, "is_active": True},
        headers=auth_headers(token),
    )
    rule_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/rules/{rule_id}",
        json={
            "name": "Updated",
            "frequency_minutes": 30,
            "include_keywords": "python,fastapi",
            "is_active": False,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Updated"
    assert payload["frequency_minutes"] == 30
    assert payload["include_keywords"] == "python,fastapi"
    assert payload["is_active"] is False


def test_update_rule_not_found() -> None:
    """Updating a non-existent rule returns 404."""
    client = create_test_client()
    token = register_and_login(client, "updatenotfound@example.com")

    response = client.patch(
        "/api/v1/rules/99999",
        json={"name": "No Such Rule"},
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_update_rule_access_control() -> None:
    """Users cannot update other users' rules."""
    client = create_test_client()
    token_a = register_and_login(client, "owner-update@example.com")
    token_b = register_and_login(client, "intruder-update@example.com")

    create_response = client.post(
        "/api/v1/rules",
        json={"name": "Protected Rule", "frequency_minutes": 60},
        headers=auth_headers(token_a),
    )
    rule_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/rules/{rule_id}",
        json={"name": "Hacked"},
        headers=auth_headers(token_b),
    )

    assert response.status_code == 404


def test_update_rule_validates_frequency() -> None:
    """Update rejects invalid frequency_minutes."""
    client = create_test_client()
    token = register_and_login(client, "badfreq@example.com")

    create_response = client.post(
        "/api/v1/rules",
        json={"name": "Valid Rule", "frequency_minutes": 60},
        headers=auth_headers(token),
    )
    rule_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/rules/{rule_id}",
        json={"frequency_minutes": 0},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_update_rule_validates_keywords() -> None:
    """Update rejects empty keywords."""
    client = create_test_client()
    token = register_and_login(client, "badkw@example.com")

    create_response = client.post(
        "/api/v1/rules",
        json={"name": "Valid Rule", "frequency_minutes": 60},
        headers=auth_headers(token),
    )
    rule_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/rules/{rule_id}",
        json={"include_keywords": ""},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


# -----------------------------------------------------------------------------
# Delete Rule Tests
# -----------------------------------------------------------------------------


def test_delete_rule() -> None:
    """Users can delete their own rules."""
    client = create_test_client()
    token = register_and_login(client, "delete@example.com")

    create_response = client.post(
        "/api/v1/rules",
        json={"name": "To Delete", "frequency_minutes": 60},
        headers=auth_headers(token),
    )
    rule_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/rules/{rule_id}", headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == rule_id
    assert payload["name"] == "To Delete"

    # Verify it's gone
    get_response = client.get(f"/api/v1/rules/{rule_id}", headers=auth_headers(token))
    assert get_response.status_code == 404


def test_delete_rule_not_found() -> None:
    """Deleting a non-existent rule returns 404."""
    client = create_test_client()
    token = register_and_login(client, "deletenotfound@example.com")

    response = client.delete("/api/v1/rules/99999", headers=auth_headers(token))

    assert response.status_code == 404


def test_delete_rule_access_control() -> None:
    """Users cannot delete other users' rules."""
    client = create_test_client()
    token_a = register_and_login(client, "owner-delete@example.com")
    token_b = register_and_login(client, "intruder-delete@example.com")

    create_response = client.post(
        "/api/v1/rules",
        json={"name": "Protected Delete", "frequency_minutes": 60},
        headers=auth_headers(token_a),
    )
    rule_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/rules/{rule_id}", headers=auth_headers(token_b))

    assert response.status_code == 404

    # Verify it still exists for owner
    get_response = client.get(f"/api/v1/rules/{rule_id}", headers=auth_headers(token_a))
    assert get_response.status_code == 200
