"""
Shared OpenAPI metadata for PDF Tools.

These definitions keep endpoint documentation consistent without changing
runtime exception handling or response behavior.
"""

from typing import Any

from app.models.error import ErrorResponse

STANDARD_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "model": ErrorResponse,
        "description": "The request or uploaded PDF is invalid.",
    },
    401: {
        "model": ErrorResponse,
        "description": "A valid PDF Tools API key is required.",
    },
    403: {
        "model": ErrorResponse,
        "description": "The authenticated client lacks the required permission.",
    },
    409: {
        "model": ErrorResponse,
        "description": "The requested output conflicts with an existing resource.",
    },
    413: {
        "model": ErrorResponse,
        "description": "The uploaded file exceeds the configured size limit.",
    },
    415: {
        "model": ErrorResponse,
        "description": "The uploaded file uses an unsupported media type.",
    },
    422: {
        "model": ErrorResponse,
        "description": "FastAPI could not validate the submitted request.",
    },
    500: {
        "model": ErrorResponse,
        "description": "An unexpected internal server error occurred.",
    },
}


AUTHENTICATED_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status_code: response for status_code, response in STANDARD_ERROR_RESPONSES.items()
}


PUBLIC_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status_code: response
    for status_code, response in STANDARD_ERROR_RESPONSES.items()
    if status_code not in {401, 403}
}


ERROR_RESPONSE_EXAMPLE = {
    "success": False,
    "request_id": "a15abfc2-7a74-4c58-9272-c31d797d5354",
    "timestamp": "2026-07-16T19:49:33.654966Z",
    "error": {
        "code": "PDFT-1101",
        "message": "An API key is required.",
        "details": None,
    },
}
