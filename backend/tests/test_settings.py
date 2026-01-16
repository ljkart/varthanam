"""Tests for application settings validation and defaults."""

from __future__ import annotations

import pytest
from app.core.settings import Settings
from pydantic import ValidationError


def test_settings_missing_required_env_vars_fail_fast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing required environment variables should raise a clear error."""
    for key in (
        "ENV",
        "APP_ENVIRONMENT",
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "JWT_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ValidationError) as excinfo:
        Settings()

    error_fields = {error["loc"][0] for error in excinfo.value.errors()}
    assert "ENV" in error_fields
    assert "DATABASE_URL" in error_fields
    assert "JWT_SECRET_KEY" in error_fields


def test_settings_parse_valid_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should parse and coerce valid environment variables."""
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///./varthanam.db")
    monkeypatch.setenv("JWT_SECRET_KEY", "dev-secret")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "45")
    monkeypatch.setenv("JWT_ALGORITHM", "HS512")

    settings = Settings()

    assert settings.environment == "dev"
    assert settings.database_url == "sqlite+pysqlite:///./varthanam.db"
    assert settings.jwt_access_token_expire_minutes == 45
    assert settings.jwt_algorithm == "HS512"


def test_test_env_defaults_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test environment should default to an in-memory database."""
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings = Settings()

    assert settings.environment == "test"
    assert settings.database_url == "sqlite+pysqlite:///:memory:"
