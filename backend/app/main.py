"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.routers.health import router as health_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI(title="Varthanam API")
    app.include_router(health_router)
    return app


app = create_app()
