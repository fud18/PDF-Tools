"""
Health-check endpoints.

The basic health endpoint is public. Detailed runtime information requires a
valid API key.
"""

import os
import platform
import socket
import time
from datetime import timedelta

import psutil
from fastapi import APIRouter, Depends, Request

from app.core.authentication import AuthenticatedClient, require_api_key
from app.core.configuration import Settings, get_settings
from app.core.responses import ok
from app.models.response import SuccessResponse

router = APIRouter(tags=["Health"])

_APPLICATION_STARTED = time.monotonic()


@router.get(
    "/health",
    summary="Check service health",
    response_model=SuccessResponse,
)
def health_check(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> SuccessResponse:
    """Return a minimal public health response."""

    return ok(
        request_id=request.state.request_id,
        data={
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "healthy",
        },
    )


@router.get(
    "/health/details",
    summary="Get detailed service health",
    response_model=SuccessResponse,
)
def detailed_health_check(
    request: Request,
    client: AuthenticatedClient = Depends(require_api_key),
    settings: Settings = Depends(get_settings),
) -> SuccessResponse:
    """Return authenticated runtime and resource information."""

    request.state.authenticated_client = client.name

    process = psutil.Process(os.getpid())
    memory = process.memory_info()

    uptime_seconds = int(time.monotonic() - _APPLICATION_STARTED)

    return ok(
        request_id=request.state.request_id,
        data={
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "status": "healthy",
            "authenticated_client": client.name,
            "runtime": {
                "hostname": socket.gethostname(),
                "python_version": platform.python_version(),
                "process_id": os.getpid(),
                "worker_configuration": settings.worker_count,
                "uptime_seconds": uptime_seconds,
                "uptime": str(timedelta(seconds=uptime_seconds)),
            },
            "memory": {
                "resident_bytes": memory.rss,
                "virtual_bytes": memory.vms,
            },
        },
    )
