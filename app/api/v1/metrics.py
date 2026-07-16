"""
Prometheus metrics endpoint.

Metrics contain operational measurements only. They do not contain PDF
contents, filenames, form-field names, form-field values, API keys, or other
document data.
"""

from fastapi import APIRouter, Depends, Request, Response

from app.core.authentication import AuthenticatedClient, require_api_key
from app.core.metrics import CONTENT_TYPE_LATEST, render_metrics

router = APIRouter(tags=["Observability"])


@router.get(
    "/metrics",
    summary="Export Prometheus metrics",
    description=(
        "Returns authenticated, Prometheus-compatible service metrics. "
        "The response uses the Prometheus text exposition format."
    ),
    response_class=Response,
    responses={
        200: {
            "description": "Prometheus text exposition data.",
            "content": {
                "text/plain": {
                    "example": (
                        "# HELP pdf_tools_http_requests_total "
                        "Total HTTP requests processed by PDF Tools.\n"
                    )
                }
            },
        }
    },
)
def metrics_endpoint(
    request: Request,
    client: AuthenticatedClient = Depends(require_api_key),
) -> Response:
    """Return aggregated service metrics for all active workers."""

    request.state.authenticated_client = client.name

    return Response(
        content=render_metrics(),
        headers={
            "Content-Type": CONTENT_TYPE_LATEST,
            "Cache-Control": "no-store",
        },
    )
