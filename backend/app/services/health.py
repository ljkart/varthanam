"""Service logic for application health checks."""

from app.schemas.health import HealthResponse


def get_health_status() -> HealthResponse:
    """Return the current service health status.

    Returns:
        HealthResponse: The health status payload.
    """
    return HealthResponse(status="ok")
