"""
Standard error-response models for PDF Tools.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Machine-readable and human-readable API error information."""

    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """Standard envelope for unsuccessful API responses."""

    success: bool = False
    request_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: ErrorDetail
