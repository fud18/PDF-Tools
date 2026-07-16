"""
Helpers for building standard PDF Tools API responses.
"""

from typing import Any

from app.core.version import APP_VERSION
from app.models.error import ErrorDetail, ErrorResponse
from app.models.response import SuccessResponse


def ok(
    request_id: str,
    data: Any,
) -> SuccessResponse:
    """Build a standard successful JSON response."""

    return SuccessResponse(
        request_id=request_id,
        version=APP_VERSION,
        data=data,
    )


def fail(
    request_id: str,
    code: str,
    message: str,
    details: Any | None = None,
) -> ErrorResponse:
    """Build a standard unsuccessful JSON response."""

    return ErrorResponse(
        request_id=request_id,
        error=ErrorDetail(
            code=code,
            message=message,
            details=details,
        ),
    )
