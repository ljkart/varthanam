"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.core.logging import configure_logging
from app.core.settings import Settings, get_settings
from app.routers.health import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional configuration to use for this app instance.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings)

    app = FastAPI(title=resolved_settings.app_name)
    app.include_router(health_router)
    app.state.settings = resolved_settings
    return app


app = create_app()
