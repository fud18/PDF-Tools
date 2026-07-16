"""
PDF inspection service.

The uploaded PDF is processed from an in-memory byte buffer. The service does
not create temporary files or persist the uploaded document.
"""

from io import BytesIO
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class InvalidPDFError(ValueError):
    """Raised when uploaded data is not a readable PDF document."""


def inspect_pdf(pdf_data: bytes) -> dict[str, Any]:
    """Inspect PDF metadata, pages, and interactive form fields."""

    try:
        reader = PdfReader(BytesIO(pdf_data), strict=False)
    except (PdfReadError, OSError, ValueError) as exc:
        raise InvalidPDFError("The uploaded file is not a readable PDF.") from exc

    metadata: dict[str, str | None] = {}

    if reader.metadata:
        for key, value in reader.metadata.items():
            normalized_key = str(key).lstrip("/")
            metadata[normalized_key] = None if value is None else str(value)

    form_fields = reader.get_fields() or {}
    fields: list[dict[str, Any]] = []
    signature_fields: list[str] = []

    for field_name, field_data in form_fields.items():
        field_type = field_data.get("/FT")
        field_type_text = None if field_type is None else str(field_type)

        field_entry = {
            "name": field_name,
            "type": field_type_text,
            "alternate_name": field_data.get("/TU"),
            "mapping_name": field_data.get("/TM"),
            "flags": field_data.get("/Ff"),
        }

        fields.append(field_entry)

        if field_type_text == "/Sig":
            signature_fields.append(field_name)

    return {
        "page_count": len(reader.pages),
        "encrypted": reader.is_encrypted,
        "metadata": metadata,
        "form_field_count": len(fields),
        "form_fields": fields,
        "signature_field_count": len(signature_fields),
        "signature_fields": signature_fields,
    }
