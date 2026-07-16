"""
Integration tests for the generated OpenAPI schema.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, base_url="http://localhost")


def test_openapi_schema_is_available() -> None:
    """Verify that the OpenAPI document can be generated."""

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["version"] == "0.4.0"


def test_api_key_security_scheme_is_documented() -> None:
    """Verify Swagger UI receives the X-API-Key security definition."""

    schema = client.get("/openapi.json").json()
    security_schemes = schema["components"]["securitySchemes"]

    assert "PDFToolsAPIKey" in security_schemes
    assert security_schemes["PDFToolsAPIKey"]["type"] == "apiKey"
    assert security_schemes["PDFToolsAPIKey"]["name"] == "X-API-Key"
    assert security_schemes["PDFToolsAPIKey"]["in"] == "header"


def test_standard_error_schema_is_documented() -> None:
    """Verify the reusable error response schema is published."""

    schema = client.get("/openapi.json").json()

    assert "ErrorResponse" in schema["components"]["schemas"]
    assert "ErrorDetail" in schema["components"]["schemas"]


def test_inspection_endpoint_documents_errors() -> None:
    """Verify protected PDF endpoints document common failures."""

    schema = client.get("/openapi.json").json()
    responses = schema["paths"]["/v1/pdf/inspect"]["post"]["responses"]

    for status_code in ("400", "401", "403", "413", "415", "422", "500"):
        assert status_code in responses


def test_fill_endpoint_documents_pdf_response() -> None:
    """Verify the form-fill endpoint documents binary PDF output."""

    schema = client.get("/openapi.json").json()
    success = schema["paths"]["/v1/pdf/fill"]["post"]["responses"]["200"]

    assert "application/pdf" in success["content"]


def test_metrics_endpoint_documents_text_response() -> None:
    """Verify the metrics endpoint documents Prometheus output."""

    schema = client.get("/openapi.json").json()
    success = schema["paths"]["/v1/metrics"]["get"]["responses"]["200"]

    assert "text/plain" in success["content"]
