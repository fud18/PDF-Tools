"""
PDF Tools FastAPI application.

PDF Tools provides reusable, authenticated PDF-processing endpoints for
internal automation projects.
"""

from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import router as v1_router
from app.core.configuration import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware

settings = get_settings()

configure_logging(settings.log_level)

tags_metadata = [
    {
        "name": "Health",
        "description": ("Public service availability and authenticated runtime diagnostics."),
    },
    {
        "name": "Observability",
        "description": ("Authenticated Prometheus metrics and operational service telemetry."),
    },
    {
        "name": "PDF Inspection",
        "description": (
            "Inspect PDF metadata, page counts, AcroForm fields, field types, "
            "encryption state, and signature fields."
        ),
    },
    {
        "name": "PDF Forms",
        "description": ("Fill and optionally flatten interactive AcroForm PDF documents."),
    },
]

app = FastAPI(
    title=settings.app_name,
    summary="Secure internal PDF-processing API",
    description=(
        "PDF Tools is a reusable internal REST API for inspecting and "
        "processing PDF documents.\n\n"
        "## Authentication\n\n"
        "Protected endpoints require an `X-API-Key` request header. Select "
        "**Authorize** in Swagger UI and enter a valid client API key.\n\n"
        "## Privacy\n\n"
        "Uploaded documents are processed in memory and are not intentionally "
        "persisted. PDF contents, field values, filenames, and API keys are "
        "not intentionally logged.\n\n"
        "## Request tracing\n\n"
        "Every response includes an `X-Request-ID` header. JSON responses also "
        "include the request ID in the response body."
    ),
    version=settings.app_version,
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "PDF Tools Administrator",
    },
    license_info={
        "name": "MIT License",
    },
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "filter": True,
        "persistAuthorization": True,
        "syntaxHighlight.theme": "agate",
        "tryItOutEnabled": True,
    },
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "pdf-tools.rstechwiz.net",
        "192.168.3.24",
        "127.0.0.1",
        "localhost",
    ],
)

app.add_middleware(RequestContextMiddleware)

register_exception_handlers(app)

app.include_router(v1_router)


@app.get(
    "/",
    include_in_schema=False,
)
def root() -> dict[str, str]:
    """Return basic service information."""

    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "health": "/v1/health",
    }
