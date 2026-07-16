"""
Request middleware for PDF Tools.

Each request receives an X-Request-ID value. Requests are logged with
operational metadata without recording document contents, field values,
filenames, or API keys.
"""

import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.types import ASGIApp

logger = logging.getLogger("pdf_tools.requests")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Add request IDs, timing data, and sanitized request logging."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process one request and add operational context."""

        incoming_request_id = request.headers.get(
            "X-Request-ID",
            "",
        ).strip()

        request_id = incoming_request_id[:128] if incoming_request_id else str(uuid.uuid4())

        request.state.request_id = request_id

        content_length_header = request.headers.get("content-length")
        input_bytes: int | None = None

        if content_length_header and content_length_header.isdigit():
            input_bytes = int(content_length_header)

        started = time.perf_counter()

        try:
            response: Response = await call_next(request)
        except Exception:
            duration_ms = round(
                (time.perf_counter() - started) * 1000,
                3,
            )

            logger.exception(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                    "input_bytes": input_bytes,
                },
            )
            raise

        duration_ms = round(
            (time.perf_counter() - started) * 1000,
            3,
        )

        response.headers["X-Request-ID"] = request_id

        output_length_header = response.headers.get("content-length")
        output_bytes: int | None = None

        if output_length_header and output_length_header.isdigit():
            output_bytes = int(output_length_header)

        client_name = getattr(
            request.state,
            "authenticated_client",
            None,
        )

        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "client": client_name,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "input_bytes": input_bytes,
                "output_bytes": output_bytes,
            },
        )

        return response
