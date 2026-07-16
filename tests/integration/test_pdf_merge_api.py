"""
Integration tests for the authenticated PDF merge endpoint.
"""

import hashlib
import json
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from pypdf import PdfReader, PdfWriter

from app.core.configuration import get_settings
from app.main import app

client = TestClient(
    app,
    base_url="http://localhost",
)


def create_pdf(
    width: float,
    height: float,
    rotation: int = 0,
) -> bytes:
    """Create a one-page PDF for API testing."""

    writer = PdfWriter()
    page = writer.add_blank_page(width=width, height=height)

    if rotation:
        page.rotate(rotation)

    output = BytesIO()
    writer.write(output)

    return output.getvalue()


def configure_test_client(
    temporary_path: Path,
    monkeypatch,
    *,
    permissions: list[str],
) -> str:
    """Create a temporary API client configuration."""

    api_key = "pdf-tools-merge-integration-key"
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    clients_file = temporary_path / "clients.json"

    clients_file.write_text(
        json.dumps(
            {
                "clients": [
                    {
                        "name": "integration-test",
                        "enabled": True,
                        "key_sha256": key_hash,
                        "permissions": permissions,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "PDFTOOLS_CLIENTS_FILE",
        str(clients_file),
    )

    get_settings.cache_clear()

    return api_key


def test_merge_requires_authentication() -> None:
    """Verify missing API credentials are rejected."""

    first = create_pdf(100, 200)
    second = create_pdf(300, 400)

    response = client.post(
        "/v1/pdf/merge",
        files=[
            ("files", ("first.pdf", first, "application/pdf")),
            ("files", ("second.pdf", second, "application/pdf")),
        ],
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "PDFT-1101"


def test_merge_requires_pdf_merge_permission(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify clients without pdf.merge receive a forbidden response."""

    api_key = configure_test_client(
        tmp_path,
        monkeypatch,
        permissions=["pdf.inspect"],
    )

    first = create_pdf(100, 200)
    second = create_pdf(300, 400)

    try:
        response = client.post(
            "/v1/pdf/merge",
            headers={"X-API-Key": api_key},
            files=[
                ("files", ("first.pdf", first, "application/pdf")),
                ("files", ("second.pdf", second, "application/pdf")),
            ],
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PDFT-1102"


def test_merge_returns_pdf_in_submitted_order(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify authenticated merging preserves page order and geometry."""

    api_key = configure_test_client(
        tmp_path,
        monkeypatch,
        permissions=["pdf.merge"],
    )

    first = create_pdf(100, 200, 90)
    second = create_pdf(300, 400, 180)

    try:
        response = client.post(
            "/v1/pdf/merge",
            headers={"X-API-Key": api_key},
            files=[
                ("files", ("first.pdf", first, "application/pdf")),
                ("files", ("second.pdf", second, "application/pdf")),
            ],
            data={
                "output_name": "SSYFL League Packet",
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["x-pdf-files-merged"] == "2"
    assert response.headers["x-pdf-page-count"] == "2"
    assert response.headers["x-request-id"]
    assert (
        response.headers["content-disposition"] == 'attachment; filename="SSYFL_League_Packet.pdf"'
    )

    reader = PdfReader(BytesIO(response.content))

    assert len(reader.pages) == 2
    assert float(reader.pages[0].mediabox.width) == 100.0
    assert float(reader.pages[0].mediabox.height) == 200.0
    assert int(reader.pages[0].rotation) == 90
    assert float(reader.pages[1].mediabox.width) == 300.0
    assert float(reader.pages[1].mediabox.height) == 400.0
    assert int(reader.pages[1].rotation) == 180


def test_merge_rejects_single_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verify fewer than two PDFs return a standard error envelope."""

    api_key = configure_test_client(
        tmp_path,
        monkeypatch,
        permissions=["pdf.merge"],
    )

    document = create_pdf(100, 200)

    try:
        response = client.post(
            "/v1/pdf/merge",
            headers={"X-API-Key": api_key},
            files=[
                ("files", ("only.pdf", document, "application/pdf")),
            ],
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PDFT-1003"


def test_merge_is_documented_in_openapi() -> None:
    """Verify the merge operation and binary response are documented."""

    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/v1/pdf/merge"]["post"]

    assert "PDF Merge" in operation["tags"]
    assert "application/pdf" in operation["responses"]["200"]["content"]
    assert operation["security"] == [{"PDFToolsAPIKey": []}]
