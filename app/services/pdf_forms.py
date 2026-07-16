"""
PDF AcroForm filling service.

Input and output documents are processed using in-memory byte buffers. The
service does not create temporary files or persist uploaded PDF documents.
"""

from io import BytesIO
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError
from pypdf.generic import NameObject


class InvalidPDFFormError(ValueError):
    """Raised when a PDF cannot be processed as an AcroForm document."""


class EncryptedPDFError(InvalidPDFFormError):
    """Raised when an encrypted PDF cannot be processed."""


class MissingFormFieldsError(InvalidPDFFormError):
    """Raised when the PDF does not contain interactive form fields."""


class UnknownFormFieldsError(InvalidPDFFormError):
    """Raised when the request references fields absent from the PDF."""

    def __init__(self, unknown_field_count: int) -> None:
        super().__init__(
            f"The field mapping contains {unknown_field_count} "
            "field(s) that do not exist in the PDF."
        )
        self.unknown_field_count = unknown_field_count


def _normalize_field_value(value: Any) -> str:
    """
    Normalize a JSON-compatible value for pypdf.

    Boolean values use common AcroForm checkbox states. Clients may send an
    explicit string when a checkbox uses a custom export value.
    """

    if value is None:
        return ""

    if isinstance(value, bool):
        return "/Yes" if value else "/Off"

    return str(value)


def _remove_acroform(writer: PdfWriter) -> None:
    """
    Remove the AcroForm dictionary after widgets have been flattened.

    Once widget annotations are converted into regular page content and
    removed, the AcroForm field tree is no longer needed. Removing it avoids
    retaining dangling or null form-field references in the output PDF.
    """

    root_object = writer.root_object
    acroform_key = NameObject("/AcroForm")

    if acroform_key in root_object:
        del root_object[acroform_key]


def fill_pdf_form(
    pdf_data: bytes,
    field_values: dict[str, Any],
    *,
    flatten: bool,
    strict_fields: bool,
) -> tuple[bytes, int, int]:
    """
    Fill an AcroForm PDF and return the resulting PDF bytes.

    Returns:
        A tuple containing:
        - Completed PDF bytes
        - Number of supplied field mappings applied
        - Number of unknown fields ignored
    """

    try:
        reader = PdfReader(BytesIO(pdf_data), strict=False)
    except (PdfReadError, OSError, ValueError) as exc:
        raise InvalidPDFFormError("The uploaded file is not a readable PDF.") from exc

    if reader.is_encrypted:
        raise EncryptedPDFError("Encrypted PDFs are not supported by this endpoint.")

    try:
        existing_fields = reader.get_fields() or {}
    except Exception as exc:
        raise InvalidPDFFormError("The PDF form-field structure could not be read.") from exc

    if not existing_fields:
        raise MissingFormFieldsError("The uploaded PDF does not contain AcroForm fields.")

    requested_names = set(field_values)
    existing_names = set(existing_fields)
    unknown_names = requested_names - existing_names

    if strict_fields and unknown_names:
        raise UnknownFormFieldsError(len(unknown_names))

    applicable_values = {
        field_name: _normalize_field_value(field_value)
        for field_name, field_value in field_values.items()
        if field_name in existing_names
    }

    try:
        writer = PdfWriter(clone_from=reader)

        for page in writer.pages:
            writer.update_page_form_field_values(
                page,
                applicable_values,
                auto_regenerate=False,
                flatten=flatten,
            )

        if flatten:
            writer.remove_annotations(subtypes="/Widget")
            _remove_acroform(writer)

        output_buffer = BytesIO()
        writer.write(output_buffer)

    except Exception as exc:
        raise InvalidPDFFormError("The PDF form could not be filled.") from exc

    return (
        output_buffer.getvalue(),
        len(applicable_values),
        len(unknown_names),
    )
