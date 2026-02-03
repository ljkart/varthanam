"""FastAPI application entrypoint."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.settings import Settings, get_settings
from app.routers.articles import router as articles_router
from app.routers.auth import router as auth_router
from app.routers.collections import router as collections_router
from app.routers.feeds import router as feeds_router
from app.routers.health import router as health_router
from app.routers.rules import router as rules_router


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
    register_exception_handlers(app)

    # CORS middleware for frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_router = APIRouter(prefix="/api/v1")
    api_router.include_router(health_router)
    api_router.include_router(auth_router)
    api_router.include_router(collections_router)
    api_router.include_router(feeds_router)
    api_router.include_router(articles_router)
    api_router.include_router(rules_router)
    app.include_router(api_router)

    # Deprecated: keep legacy routes temporarily while clients migrate.
    app.include_router(health_router, include_in_schema=False)
    app.include_router(auth_router, include_in_schema=False)
    app.include_router(collections_router, include_in_schema=False)
    app.include_router(feeds_router, include_in_schema=False)
    app.include_router(articles_router, include_in_schema=False)
    app.include_router(rules_router, include_in_schema=False)
    app.state.settings = resolved_settings
    return app


app = create_app()
