"""
Unit tests for metrics helpers.
"""

from app.core.metrics import normalize_route, record_request, render_metrics


class ExampleRoute:
    """Minimal route object used to test route normalization."""

    path = "/v1/example/{identifier}"


def test_normalize_route_uses_route_template() -> None:
    """Verify route templates are used instead of raw request paths."""

    result = normalize_route({"route": ExampleRoute()})

    assert result == "/v1/example/{identifier}"


def test_normalize_route_uses_safe_fallback() -> None:
    """Verify unmatched routes use a bounded fallback label."""

    result = normalize_route({})

    assert result == "unmatched"


def test_render_metrics_contains_pdf_tools_metrics() -> None:
    """Verify custom metrics appear in Prometheus output."""

    record_request(
        method="GET",
        route="/v1/test",
        status_code=200,
        duration_seconds=0.01,
        input_bytes=10,
        output_bytes=20,
    )

    output = render_metrics().decode("utf-8")

    assert "pdf_tools_http_requests_total" in output
    assert "pdf_tools_http_request_duration_seconds" in output
    assert "pdf_tools_http_bytes_total" in output
