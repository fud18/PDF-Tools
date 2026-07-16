"""
PDF inspection API endpoint.

Uploaded PDF data is read directly into memory and is never intentionally
written to disk.
"""

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)

from app.core.authentication import AuthenticatedClient, require_permission
from app.core.configuration import Settings, get_settings
from app.core.responses import ok
from app.models.response import SuccessResponse
from app.services.pdf_inspection import InvalidPDFError, inspect_pdf

router = APIRouter(tags=["PDF Inspection"])


@router.post(
    "/inspect",
    summary="Inspect a PDF document",
    description=(
        "Returns page count, PDF metadata, AcroForm field definitions, "
        "field types, and signature fields."
    ),
    response_model=SuccessResponse,
)
async def inspect_pdf_endpoint(
    request: Request,
    file: UploadFile = File(
        ...,
        description="PDF document to inspect",
    ),
    client: AuthenticatedClient = Depends(require_permission("pdf.inspect")),
    settings: Settings = Depends(get_settings),
) -> SuccessResponse:
    """Return PDF metadata, form fields, and signature fields."""

    content_type = (file.content_type or "").lower()

    if content_type not in {
        "application/pdf",
        "application/octet-stream",
    }:
        await file.close()

        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are accepted.",
        )

    pdf_data = await file.read(settings.max_upload_bytes + 1)
    await file.close()

    if len(pdf_data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The uploaded PDF exceeds the configured size limit.",
        )

    if not pdf_data.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file does not contain a valid PDF header.",
        )

    try:
        result = inspect_pdf(pdf_data)
    except InvalidPDFError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ok(
        request_id=request.state.request_id,
        data={
            "authenticated_client": client.name,
            **result,
        },
    )
