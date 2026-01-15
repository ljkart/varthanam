"""API routes for health checks."""

from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health import get_health_status

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return a lightweight health check response.

    Returns:
        HealthResponse: The current health status.
    """
    return get_health_status()
