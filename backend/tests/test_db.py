"""Tests for database configuration and session helpers."""

from app.core.settings import Settings
from app.db.session import get_db_session, get_engine


def test_engine_created_from_settings() -> None:
    """Engine should be created using the provided DATABASE_URL."""
    settings = Settings(
        app_name="Varthanam Test API",
        environment="test",
        log_level="INFO",
        database_url="sqlite+pysqlite:///:memory:",
        jwt_secret="test-secret",
        jwt_access_token_exp_minutes=60,
    )

    engine = get_engine(settings)

    assert engine.url.render_as_string(hide_password=False) == settings.database_url


def test_db_session_dependency_closes_session() -> None:
    """DB session dependency should close the session after use."""
    settings = Settings(
        app_name="Varthanam Test API",
        environment="test",
        log_level="INFO",
        database_url="sqlite+pysqlite:///:memory:",
        jwt_secret="test-secret",
        jwt_access_token_exp_minutes=60,
    )

    session_generator = get_db_session(settings)
    session = next(session_generator)
    connection = session.connection()

    assert session.is_active is True
    assert connection.closed is False

    session_generator.close()

    assert connection.closed is True
