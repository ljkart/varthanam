"""Schemas for the health endpoint."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response model for the health endpoint."""

    status: str
