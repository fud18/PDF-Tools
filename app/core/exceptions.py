"""
Centralized application exceptions and exception-handler registration.

All JSON errors use the standard PDF Tools response envelope and include the
request ID assigned by request middleware.
"""

import logging
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import ErrorCode
from app.core.responses import fail

logger = logging.getLogger("pdf_tools.exceptions")


class PDFToolsException(Exception):
    """Base exception for expected PDF Tools application errors."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Any | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)

        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code


def _request_id(request: Request) -> str:
    """Return the current request ID or a safe fallback value."""

    return str(getattr(request.state, "request_id", "unknown"))


def _error_code_for_http_status(status_code: int) -> ErrorCode:
    """Map common HTTP status codes to stable PDF Tools error codes."""

    mappings = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.INVALID_API_KEY,
        403: ErrorCode.PERMISSION_DENIED,
        413: ErrorCode.FILE_TOO_LARGE,
        415: ErrorCode.UNSUPPORTED_MEDIA_TYPE,
        422: ErrorCode.VALIDATION_ERROR,
        503: ErrorCode.CONFIGURATION_ERROR,
    }

    return mappings.get(status_code, ErrorCode.INTERNAL_ERROR)


async def pdf_tools_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle an explicitly raised PDF Tools exception."""

    pdf_tools_exception = cast(PDFToolsException, exc)

    payload = fail(
        request_id=_request_id(request),
        code=pdf_tools_exception.code,
        message=pdf_tools_exception.message,
        details=pdf_tools_exception.details,
    )

    return JSONResponse(
        status_code=pdf_tools_exception.status_code,
        content=payload.model_dump(mode="json"),
    )


async def http_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Convert FastAPI HTTP exceptions to the standard error envelope."""

    http_exception = cast(HTTPException, exc)

    code = _error_code_for_http_status(http_exception.status_code)

    payload = fail(
        request_id=_request_id(request),
        code=code.value,
        message=str(http_exception.detail),
    )

    return JSONResponse(
        status_code=http_exception.status_code,
        content=payload.model_dump(mode="json"),
        headers=http_exception.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return sanitized request-validation errors."""

    validation_exception = cast(RequestValidationError, exc)

    details = [
        {
            "location": list(error.get("loc", [])),
            "message": error.get("msg", "Invalid value."),
            "type": error.get("type", "validation_error"),
        }
        for error in validation_exception.errors()
    ]

    payload = fail(
        request_id=_request_id(request),
        code=ErrorCode.VALIDATION_ERROR.value,
        message="The request could not be validated.",
        details=details,
    )

    return JSONResponse(
        status_code=422,
        content=payload.model_dump(mode="json"),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a generic response for unexpected server errors."""

    logger.exception(
        "Unhandled application exception",
        extra={
            "request_id": _request_id(request),
            "method": request.method,
            "path": request.url.path,
        },
        exc_info=exc,
    )

    payload = fail(
        request_id=_request_id(request),
        code=ErrorCode.INTERNAL_ERROR.value,
        message="An unexpected server error occurred.",
    )

    return JSONResponse(
        status_code=500,
        content=payload.model_dump(mode="json"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all centralized PDF Tools exception handlers."""

    app.add_exception_handler(
        PDFToolsException,
        pdf_tools_exception_handler,
    )
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
