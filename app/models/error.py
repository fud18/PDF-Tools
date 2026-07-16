"""
Standard error-response models for PDF Tools.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """Machine-readable and human-readable API error information."""

    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """Standard envelope for unsuccessful API responses."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": False,
                    "request_id": "0ac3d197-7750-42f6-8823-1d52186127a7",
                    "timestamp": "2026-07-16T19:49:33.654966Z",
                    "error": {
                        "code": "PDFT-1101",
                        "message": "An API key is required.",
                        "details": None,
                    },
                }
            ]
        }
    )

    success: bool = False
    request_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: ErrorDetail
