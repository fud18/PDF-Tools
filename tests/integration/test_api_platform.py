"""
Integration tests for the PDF Tools production API platform.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(
    app,
    base_url="http://localhost",
)


def test_root_endpoint_returns_service_information() -> None:
    """Verify the unversioned root endpoint returns service metadata."""

    response = client.get("/")

    assert response.status_code == 200

    payload = response.json()

    assert payload["service"] == "PDF Tools"
    assert payload["version"] == "0.5.0"
    assert payload["documentation"] == "/docs"
    assert payload["openapi"] == "/openapi.json"
    assert payload["health"] == "/v1/health"


def test_public_health_endpoint_uses_standard_response_envelope() -> None:
    """Verify the public health endpoint follows the standard response model."""

    response = client.get("/v1/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers

    payload = response.json()

    assert payload["success"] is True
    assert payload["version"] == "0.5.0"
    assert payload["request_id"] == response.headers["X-Request-ID"]
    assert payload["data"]["service"] == "PDF Tools"
    assert payload["data"]["version"] == "0.5.0"
    assert payload["data"]["status"] == "healthy"


def test_incoming_request_id_is_preserved() -> None:
    """Verify a caller-provided request ID is preserved in the response."""

    request_id = "integration-test-request-id"

    response = client.get(
        "/v1/health",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    assert response.json()["request_id"] == request_id


def test_request_id_is_limited_to_128_characters() -> None:
    """Verify oversized caller-provided request IDs are safely truncated."""

    request_id = "a" * 256

    response = client.get(
        "/v1/health",
        headers={
            "X-Request-ID": request_id,
        },
    )

    returned_request_id = response.headers["X-Request-ID"]

    assert response.status_code == 200
    assert len(returned_request_id) == 128
    assert returned_request_id == request_id[:128]


def test_authenticated_health_endpoint_rejects_missing_api_key() -> None:
    """Verify protected health details reject unauthenticated access."""

    response = client.get("/v1/health/details")

    assert response.status_code == 401

    payload = response.json()

    assert payload["success"] is False
    assert payload["error"]["code"] == "PDFT-1101"
    assert payload["request_id"] == response.headers["X-Request-ID"]


def test_metrics_endpoint_rejects_missing_api_key() -> None:
    """Verify metrics cannot be retrieved without authentication."""

    response = client.get("/v1/metrics")

    assert response.status_code == 401

    payload = response.json()

    assert payload["success"] is False
    assert payload["error"]["code"] == "PDFT-1101"


def test_unknown_route_returns_request_id_header() -> None:
    """Verify unknown routes still include request tracing metadata."""

    response = client.get("/v1/does-not-exist")

    assert response.status_code == 404
    assert "X-Request-ID" in response.headers
