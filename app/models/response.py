"""
Standard success-response models for PDF Tools.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    """Standard envelope for successful JSON API responses."""

    success: bool = True
    request_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: str
    data: Any
