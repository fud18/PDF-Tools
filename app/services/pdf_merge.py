"""
In-memory PDF merge service.

Uploaded PDF documents and the completed PDF are processed using byte buffers.
The service does not intentionally create temporary files, persist documents,
or expose document names or contents through logging.
"""

import re
from io import BytesIO

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError


class PDFMergeError(ValueError):
    """Base exception for PDF merge failures."""


class TooFewPDFsError(PDFMergeError):
    """Raised when fewer than two PDF documents are supplied."""


class InvalidPDFMergeError(PDFMergeError):
    """Raised when an input cannot be processed as a PDF."""


class EncryptedPDFMergeError(PDFMergeError):
    """Raised when an encrypted PDF is supplied."""


def sanitize_output_name(output_name: str | None) -> str:
    """
    Return a safe attachment filename.

    Directory components, control characters, header delimiters, and other
    unsafe characters are removed. The result always has a .pdf extension.
    """

    if output_name is None or not output_name.strip():
        return "merged.pdf"

    candidate = output_name.strip()

    candidate = candidate.replace("\\", "/").split("/")[-1]
    candidate = re.sub(r"[\x00-\x1f\x7f]", "", candidate)
    candidate = re.sub(r"[^A-Za-z0-9._-]+", "_", candidate)
    candidate = candidate.strip("._-")

    if candidate.lower().endswith(".pdf"):
        candidate = candidate[:-4].rstrip("._-")

    candidate = candidate[:120].rstrip("._-")

    if not candidate:
        return "merged.pdf"

    return f"{candidate}.pdf"


def merge_pdf_documents(
    pdf_documents: list[bytes],
) -> tuple[bytes, int]:
    """
    Merge PDF byte sequences in their submitted order.

    Page media boxes, crop boxes, dimensions, and rotation values are retained
    by copying each source page into the output writer without rasterization.

    Returns:
        A tuple containing the merged PDF bytes and total output page count.
    """

    if len(pdf_documents) < 2:
        raise TooFewPDFsError("At least two PDF files are required.")

    writer = PdfWriter()
    total_pages = 0

    for position, pdf_data in enumerate(pdf_documents, start=1):
        try:
            reader = PdfReader(
                BytesIO(pdf_data),
                strict=False,
            )
        except (PdfReadError, OSError, ValueError) as exc:
            raise InvalidPDFMergeError(f"PDF file number {position} could not be read.") from exc

        if reader.is_encrypted:
            raise EncryptedPDFMergeError(f"PDF file number {position} is encrypted.")

        try:
            page_count = len(reader.pages)

            if page_count < 1:
                raise InvalidPDFMergeError(f"PDF file number {position} contains no pages.")

            writer.append(reader)
            total_pages += page_count
        except InvalidPDFMergeError:
            raise
        except Exception as exc:
            raise InvalidPDFMergeError(f"PDF file number {position} could not be merged.") from exc

    try:
        output_buffer = BytesIO()
        writer.write(output_buffer)
    except Exception as exc:
        raise PDFMergeError("The merged PDF could not be generated.") from exc

    return output_buffer.getvalue(), total_pages
