"""
Prometheus metrics for PDF Tools.

The metric definitions in this module support Uvicorn's multiprocess worker
model when PROMETHEUS_MULTIPROC_DIR is configured before startup.
"""

import os
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any, cast

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    multiprocess,
)

HTTP_REQUESTS_TOTAL = Counter(
    "pdf_tools_http_requests_total",
    "Total HTTP requests processed by PDF Tools.",
    labelnames=("method", "route", "status_code"),
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "pdf_tools_http_request_duration_seconds",
    "HTTP request processing duration in seconds.",
    labelnames=("method", "route"),
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
        10.0,
    ),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "pdf_tools_http_requests_in_progress",
    "HTTP requests currently being processed.",
    labelnames=("method",),
    multiprocess_mode="livesum",
)

HTTP_BYTES_TOTAL = Counter(
    "pdf_tools_http_bytes_total",
    "Total HTTP request and response bytes observed.",
    labelnames=("direction",),
)


def normalize_route(request_scope: MutableMapping[str, Any]) -> str:
    """
    Return the matched route template without exposing raw request paths.

    Route templates prevent unbounded labels containing identifiers, filenames,
    scanner paths, or other user-controlled values.
    """

    route = request_scope.get("route")
    route_path = getattr(route, "path", None)

    if isinstance(route_path, str) and route_path:
        return route_path

    return "unmatched"


def record_request(
    *,
    method: str,
    route: str,
    status_code: int,
    duration_seconds: float,
    input_bytes: int | None,
    output_bytes: int | None,
) -> None:
    """Record sanitized HTTP request measurements."""

    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        route=route,
        status_code=str(status_code),
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        route=route,
    ).observe(duration_seconds)

    if input_bytes is not None:
        HTTP_BYTES_TOTAL.labels(direction="input").inc(input_bytes)

    if output_bytes is not None:
        HTTP_BYTES_TOTAL.labels(direction="output").inc(output_bytes)


def render_metrics() -> bytes:
    """Render metrics in the Prometheus text exposition format."""

    multiprocess_directory = os.environ.get("PROMETHEUS_MULTIPROC_DIR")

    if multiprocess_directory and Path(multiprocess_directory).is_dir():
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)

        return cast(
            bytes,
            generate_latest(registry),
        )

    return cast(
        bytes,
        generate_latest(REGISTRY),
    )


__all__ = [
    "CONTENT_TYPE_LATEST",
    "HTTP_REQUESTS_IN_PROGRESS",
    "normalize_route",
    "record_request",
    "render_metrics",
]
