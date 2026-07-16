"""
Request middleware for PDF Tools.

Each request receives an X-Request-ID value. Requests are logged and measured
using operational metadata without recording document contents, field values,
filenames, API keys, or user-supplied URL values.
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

from app.core.metrics import (
    HTTP_REQUESTS_IN_PROGRESS,
    normalize_route,
    record_request,
)

logger = logging.getLogger("pdf_tools.requests")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Add request IDs, timing data, metrics, and sanitized request logging."""

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

        method = request.method
        started = time.perf_counter()

        HTTP_REQUESTS_IN_PROGRESS.labels(method=method).inc()

        try:
            response: Response = await call_next(request)
        except Exception:
            duration_seconds = time.perf_counter() - started
            route = normalize_route(request.scope)

            record_request(
                method=method,
                route=route,
                status_code=500,
                duration_seconds=duration_seconds,
                input_bytes=input_bytes,
                output_bytes=None,
            )

            logger.exception(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": route,
                    "status_code": 500,
                    "duration_ms": round(duration_seconds * 1000, 3),
                    "input_bytes": input_bytes,
                },
            )
            raise
        finally:
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method).dec()

        duration_seconds = time.perf_counter() - started
        duration_ms = round(duration_seconds * 1000, 3)

        response.headers["X-Request-ID"] = request_id

        output_length_header = response.headers.get("content-length")
        output_bytes: int | None = None

        if output_length_header and output_length_header.isdigit():
            output_bytes = int(output_length_header)

        route = normalize_route(request.scope)

        record_request(
            method=method,
            route=route,
            status_code=response.status_code,
            duration_seconds=duration_seconds,
            input_bytes=input_bytes,
            output_bytes=output_bytes,
        )

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
                "method": method,
                "path": route,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "input_bytes": input_bytes,
                "output_bytes": output_bytes,
            },
        )

        return response
