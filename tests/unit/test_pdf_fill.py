"""Unit tests for the PDF AcroForm filling service."""

from io import BytesIO

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from app.services.pdf_forms import (
    UnknownFormFieldsError,
    fill_pdf_form,
)


def create_test_form() -> bytes:
    """Create a small in-memory AcroForm PDF for testing."""

    output = BytesIO()

    document = canvas.Canvas(output)
    document.drawString(72, 750, "First Name")
    document.acroForm.textfield(
        name="FirstName",
        x=150,
        y=735,
        width=200,
        height=24,
    )

    document.drawString(72, 700, "Approved")
    document.acroForm.checkbox(
        name="Approved",
        x=150,
        y=690,
        buttonStyle="check",
        checked=False,
    )

    document.save()

    return output.getvalue()


def test_fill_pdf_form_updates_text_field() -> None:
    """Verify that a text field can be filled."""

    source_pdf = create_test_form()

    completed_pdf, fields_applied, ignored = fill_pdf_form(
        source_pdf,
        {
            "FirstName": "Cory",
            "Approved": True,
        },
        flatten=False,
        strict_fields=True,
    )

    reader = PdfReader(BytesIO(completed_pdf))
    fields = reader.get_fields()

    assert fields is not None
    assert fields["FirstName"]["/V"] == "Cory"
    assert str(fields["Approved"]["/V"]) == "/Yes"
    assert fields_applied == 2
    assert ignored == 0


def test_unknown_field_is_rejected_in_strict_mode() -> None:
    """Verify that strict mode rejects unknown form-field names."""

    source_pdf = create_test_form()

    try:
        fill_pdf_form(
            source_pdf,
            {
                "DoesNotExist": "Value",
            },
            flatten=False,
            strict_fields=True,
        )
    except UnknownFormFieldsError as exc:
        assert exc.unknown_field_count == 1
    else:
        raise AssertionError("UnknownFormFieldsError was not raised")


def test_unknown_field_can_be_ignored() -> None:
    """Verify that non-strict mode ignores unknown form fields."""

    source_pdf = create_test_form()

    _, fields_applied, ignored = fill_pdf_form(
        source_pdf,
        {
            "FirstName": "Cory",
            "DoesNotExist": "Value",
        },
        flatten=False,
        strict_fields=False,
    )

    assert fields_applied == 1
    assert ignored == 1


def test_flatten_removes_interactive_fields() -> None:
    """Verify that flattening removes interactive form widgets."""

    source_pdf = create_test_form()

    completed_pdf, _, _ = fill_pdf_form(
        source_pdf,
        {
            "FirstName": "Cory",
            "Approved": True,
        },
        flatten=True,
        strict_fields=True,
    )

    reader = PdfReader(BytesIO(completed_pdf))
    fields = reader.get_fields() or {}

    assert fields == {}
