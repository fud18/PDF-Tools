"""
Unit tests for in-memory PDF merging.
"""

from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter

from app.services.pdf_merge import (
    EncryptedPDFMergeError,
    TooFewPDFsError,
    merge_pdf_documents,
    sanitize_output_name,
)


def create_pdf(
    pages: list[tuple[float, float, int]],
) -> bytes:
    """Create a PDF with selected dimensions and rotations."""

    writer = PdfWriter()

    for width, height, rotation in pages:
        page = writer.add_blank_page(
            width=width,
            height=height,
        )

        if rotation:
            page.rotate(rotation)

    output = BytesIO()
    writer.write(output)

    return output.getvalue()


def create_encrypted_pdf() -> bytes:
    """Create a one-page encrypted PDF."""

    writer = PdfWriter()
    writer.add_blank_page(width=100, height=200)
    writer.encrypt("test-password")

    output = BytesIO()
    writer.write(output)

    return output.getvalue()


def test_merge_preserves_order_dimensions_and_rotation() -> None:
    """Verify source pages remain in submitted order and retain geometry."""

    first = create_pdf(
        [
            (100, 200, 90),
            (110, 210, 0),
        ]
    )
    second = create_pdf(
        [
            (300, 400, 180),
        ]
    )

    merged, total_pages = merge_pdf_documents([first, second])

    reader = PdfReader(BytesIO(merged))

    assert total_pages == 3
    assert len(reader.pages) == 3

    expected = [
        (100.0, 200.0, 90),
        (110.0, 210.0, 0),
        (300.0, 400.0, 180),
    ]

    actual = [
        (
            float(page.mediabox.width),
            float(page.mediabox.height),
            int(page.rotation),
        )
        for page in reader.pages
    ]

    assert actual == expected


def test_merge_rejects_fewer_than_two_documents() -> None:
    """Verify a merge requires at least two source documents."""

    document = create_pdf([(100, 200, 0)])

    with pytest.raises(TooFewPDFsError):
        merge_pdf_documents([document])


def test_merge_rejects_encrypted_documents() -> None:
    """Verify encrypted inputs are rejected."""

    regular = create_pdf([(100, 200, 0)])
    encrypted = create_encrypted_pdf()

    with pytest.raises(EncryptedPDFMergeError):
        merge_pdf_documents([regular, encrypted])


@pytest.mark.parametrize(
    ("supplied", "expected"),
    [
        (None, "merged.pdf"),
        ("", "merged.pdf"),
        ("League Packet", "League_Packet.pdf"),
        ("league.pdf", "league.pdf"),
        ("../../unsafe.pdf", "unsafe.pdf"),
        ('bad"\r\nheader.pdf', "bad_header.pdf"),
    ],
)
def test_output_name_is_sanitized(
    supplied: str | None,
    expected: str,
) -> None:
    """Verify attachment names cannot inject paths or headers."""

    assert sanitize_output_name(supplied) == expected
