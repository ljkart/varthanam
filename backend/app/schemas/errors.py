"""Schemas for standardized API error responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard API error response payload.

    Attributes:
        error_code: Stable string identifier for the error category.
        message: Human-readable summary safe to expose to clients.
        details: Optional structured metadata for troubleshooting.
    """

    error_code: str = Field(..., description="Stable error category identifier.")
    message: str = Field(..., description="Client-safe error message.")
    details: Any | None = Field(
        default=None, description="Optional structured error details."
    )
