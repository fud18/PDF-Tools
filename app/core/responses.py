from app.core.version import APP_VERSION
from app.models.error import ErrorDetail, ErrorResponse
from app.models.response import SuccessResponse


def ok(request_id: str, data):
    return SuccessResponse(
        request_id=request_id,
        version=APP_VERSION,
        data=data,
    )


def fail(request_id: str, code: str, message: str, details=None):
    return ErrorResponse(
        request_id=request_id,
        error=ErrorDetail(
            code=code,
            message=message,
            details=details,
        ),
    )
