"""
Centralized exception handlers for PDF Tools.

Responses include a request ID to make troubleshooting possible without
exposing internal stack traces or sensitive information.
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


logger = logging.getLogger("pdf_tools.exceptions")


def _request_id(request: Request) -> str | None:
    """Return the current request ID, when available."""

    return getattr(request.state, "request_id", None)


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Return a consistent response for expected HTTP errors."""

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": _request_id(request),
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return a sanitized request-validation response."""

    return JSONResponse(
        status_code=422,
        content={
            "detail": "The request could not be validated.",
            "errors": exc.errors(),
            "request_id": _request_id(request),
        },
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a generic response for unexpected exceptions."""

    logger.exception(
        "Unhandled application exception",
        extra={
            "request_id": _request_id(request),
            "method": request.method,
            "path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected server error occurred.",
            "request_id": _request_id(request),
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register the PDF Tools exception handlers."""

    app.add_exception_handler(
        HTTPException,
        http_exception_handler,
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )

    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )
