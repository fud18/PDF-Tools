"""
PDF merge API endpoint.

Multiple uploaded PDF documents are accepted through a repeated multipart
field named `files`. Documents are merged in their submitted order and are
processed entirely in memory.
"""

from io import BytesIO

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
)
from fastapi.responses import StreamingResponse

from app.core.authentication import (
    AuthenticatedClient,
    require_permission,
)
from app.core.configuration import Settings, get_settings
from app.core.errors import ErrorCode
from app.core.exceptions import PDFToolsException
from app.core.openapi import AUTHENTICATED_ERROR_RESPONSES
from app.core.version import APP_VERSION
from app.services.pdf_merge import (
    EncryptedPDFMergeError,
    InvalidPDFMergeError,
    PDFMergeError,
    TooFewPDFsError,
    merge_pdf_documents,
    sanitize_output_name,
)

router = APIRouter(tags=["PDF Merge"])


@router.post(
    "/merge",
    summary="Merge PDF documents",
    description=(
        "Accepts two or more PDF documents through the repeated multipart "
        "field `files`. Documents are merged in submitted order and returned "
        "directly as one PDF. Uploaded and completed documents are processed "
        "in memory and are not intentionally persisted."
    ),
    response_class=StreamingResponse,
    responses={
        **AUTHENTICATED_ERROR_RESPONSES,
        200: {
            "description": "Merged PDF document.",
            "content": {
                "application/pdf": {
                    "schema": {
                        "type": "string",
                        "format": "binary",
                    }
                }
            },
        },
    },
)
async def merge_pdf_endpoint(
    files: list[UploadFile] = File(
        ...,
        description=(
            "PDF documents to merge. Submit this multipart field repeatedly "
            "in the exact order the documents should appear."
        ),
    ),
    output_name: str | None = Form(
        None,
        description=(
            "Optional output filename. Unsafe path and header characters are "
            "removed, and the .pdf extension is added automatically."
        ),
        max_length=255,
    ),
    client: AuthenticatedClient = Depends(require_permission("pdf.merge")),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """Merge PDF documents and return the completed PDF."""

    del client

    file_count = len(files)

    if file_count < 2:
        for upload in files:
            await upload.close()

        raise PDFToolsException(
            code=ErrorCode.TOO_FEW_FILES.value,
            message="At least two PDF files are required.",
            details={
                "minimum_files": 2,
                "submitted_files": file_count,
            },
            status_code=422,
        )

    if file_count > settings.max_merge_files:
        for upload in files:
            await upload.close()

        raise PDFToolsException(
            code=ErrorCode.TOO_MANY_FILES.value,
            message="The request contains too many PDF files.",
            details={
                "maximum_files": settings.max_merge_files,
                "submitted_files": file_count,
            },
            status_code=413,
        )

    pdf_documents: list[bytes] = []
    total_input_bytes = 0

    try:
        for position, upload in enumerate(files, start=1):
            content_type = (upload.content_type or "").lower()

            if content_type not in {
                "application/pdf",
                "application/octet-stream",
            }:
                raise PDFToolsException(
                    code=ErrorCode.UNSUPPORTED_MEDIA_TYPE.value,
                    message=(
                        f"Uploaded file number {position} is not a supported " "PDF media type."
                    ),
                    details={
                        "file_position": position,
                    },
                    status_code=415,
                )

            remaining_bytes = settings.max_merge_request_bytes - total_input_bytes

            pdf_data = await upload.read(remaining_bytes + 1)
            total_input_bytes += len(pdf_data)

            if total_input_bytes > settings.max_merge_request_bytes:
                raise PDFToolsException(
                    code=ErrorCode.MERGE_REQUEST_TOO_LARGE.value,
                    message=(
                        "The combined PDF upload exceeds the configured " "request-size limit."
                    ),
                    details={
                        "maximum_bytes": settings.max_merge_request_bytes,
                    },
                    status_code=413,
                )

            if not pdf_data.startswith(b"%PDF-"):
                raise PDFToolsException(
                    code=ErrorCode.INVALID_PDF.value,
                    message=(
                        f"Uploaded file number {position} does not contain " "a valid PDF header."
                    ),
                    details={
                        "file_position": position,
                    },
                    status_code=400,
                )

            pdf_documents.append(pdf_data)
    finally:
        for upload in files:
            await upload.close()

    try:
        output_pdf, total_pages = merge_pdf_documents(pdf_documents)
    except TooFewPDFsError as exc:
        raise PDFToolsException(
            code=ErrorCode.TOO_FEW_FILES.value,
            message=str(exc),
            status_code=422,
        ) from exc
    except EncryptedPDFMergeError as exc:
        raise PDFToolsException(
            code=ErrorCode.ENCRYPTED_PDF.value,
            message=str(exc),
            status_code=400,
        ) from exc
    except InvalidPDFMergeError as exc:
        raise PDFToolsException(
            code=ErrorCode.INVALID_PDF.value,
            message=str(exc),
            status_code=400,
        ) from exc
    except PDFMergeError as exc:
        raise PDFToolsException(
            code=ErrorCode.PDF_MERGE_FAILED.value,
            message=str(exc),
            status_code=400,
        ) from exc

    safe_output_name = sanitize_output_name(output_name)

    response_headers = {
        "Content-Disposition": (f'attachment; filename="{safe_output_name}"'),
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
        "X-PDF-Files-Merged": str(file_count),
        "X-PDF-Page-Count": str(total_pages),
        "X-PDF-Tools-Version": APP_VERSION,
    }

    return StreamingResponse(
        BytesIO(output_pdf),
        media_type="application/pdf",
        headers=response_headers,
    )
