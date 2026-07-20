"""
Standard success-response models for PDF Tools.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SuccessResponse(BaseModel):
    """Standard envelope for successful JSON API responses."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "request_id": "59774624-ebb1-408f-beb2-54b7c6004f6a",
                    "timestamp": "2026-07-16T19:49:26.786384Z",
                    "version": "0.6.0",
                    "data": {
                        "service": "PDF Tools",
                        "version": "0.6.0",
                        "status": "healthy",
                    },
                }
            ]
        }
    )

    success: bool = True
    request_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: str
    data: Any
