"""Standardized API error handling for FastAPI routes.

The handlers in this module ensure clients always receive a consistent error
shape while preventing internal details from leaking outside the service.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.errors import ErrorResponse

logger = logging.getLogger(__name__)


def _safe_request_context(request: Request) -> dict[str, str]:
    """Capture minimal request context without leaking secrets."""
    return {"method": request.method, "path": request.url.path}


def _error_payload(
    error_code: str,
    message: str,
    details: Any | None = None,
) -> dict[str, Any]:
    """Build a standardized error payload for responses."""
    return ErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
    ).model_dump()


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Return standardized errors for FastAPI HTTPException responses."""
    details = exc.detail if not isinstance(exc.detail, str) else None
    payload = _error_payload(
        error_code="http_error",
        message=exc.detail if isinstance(exc.detail, str) else "Request failed.",
        details=details,
    )
    if exc.status_code >= 500:
        context = _safe_request_context(request)
        logger.error("HTTP exception at %(method)s %(path)s", context)
    return JSONResponse(status_code=exc.status_code, content=payload)


def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return standardized errors for request validation failures."""
    payload = _error_payload(
        error_code="validation_error",
        message="Request validation failed.",
        details=exc.errors(),
    )
    return JSONResponse(status_code=422, content=payload)


def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return safe errors for unhandled exceptions and log details server-side."""
    context = _safe_request_context(request)
    logger.exception("Unhandled exception at %(method)s %(path)s", context)
    # Mask internals to prevent leaking stack traces or sensitive data.
    payload = _error_payload(
        error_code="internal_server_error",
        message="Internal server error.",
        details=None,
    )
    return JSONResponse(status_code=500, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """Register API exception handlers on the provided FastAPI app."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
