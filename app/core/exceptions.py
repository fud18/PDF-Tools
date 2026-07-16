"""
Centralized application exceptions and exception-handler registration.

PDF Tools exceptions use stable PDFT error codes and return the standard
error response envelope without exposing internal implementation details.
"""

from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.responses import fail


class PDFToolsException(Exception):
    """Base exception for expected PDF Tools application errors."""

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)

        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code


async def pdf_tools_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return a standardized response for a PDF Tools exception."""

    pdf_tools_exception = cast(PDFToolsException, exc)

    request_id = getattr(
        request.state,
        "request_id",
        "unknown",
    )

    payload = fail(
        request_id=request_id,
        code=pdf_tools_exception.code,
        message=pdf_tools_exception.message,
        details=pdf_tools_exception.details,
    )

    return JSONResponse(
        status_code=pdf_tools_exception.status_code,
        content=payload.model_dump(mode="json"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register application-specific exception handlers."""

    app.add_exception_handler(
        PDFToolsException,
        pdf_tools_exception_handler,
    )
