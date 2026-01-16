"""Tests for the FastAPI application factory."""

from app.core.settings import Settings
from app.main import create_app


def test_create_app_uses_settings() -> None:
    """App factory should apply provided settings to the FastAPI app."""
    settings = Settings(
        app_name="Varthanam Test API", environment="test", log_level="INFO"
    )

    app = create_app(settings=settings)

    assert app.title == "Varthanam Test API"
    assert app.state.settings is settings
