from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    success: bool = True
    request_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: str
    data: Any
