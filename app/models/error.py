from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    request_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    error: ErrorDetail
