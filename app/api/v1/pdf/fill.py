"""
PDF AcroForm filling endpoint.

The endpoint accepts a PDF and a JSON field mapping in one multipart request.
Uploaded documents and field values are processed in memory and are never
intentionally logged or persisted.
"""

from io import BytesIO

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse

from app.core.authentication import (
    AuthenticatedClient,
    require_permission,
)
from app.core.configuration import Settings, get_settings
from app.models.pdf_fill import (
    InvalidFieldMappingError,
    parse_field_mapping,
)
from app.services.pdf_forms import (
    EncryptedPDFError,
    InvalidPDFFormError,
    MissingFormFieldsError,
    UnknownFormFieldsError,
    fill_pdf_form,
)


router = APIRouter(tags=["PDF Forms"])


@router.post(
    "/fill",
    summary="Fill an AcroForm PDF",
    description=(
        "Fills interactive AcroForm fields using a JSON object supplied in "
        "the multipart fields parameter. The completed PDF is returned "
        "directly and is not intentionally stored by the service."
    ),
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Completed PDF document.",
            "content": {
                "application/pdf": {},
            },
        },
        400: {
            "description": "The PDF or field mapping could not be processed.",
        },
        401: {
            "description": "An API key was not provided or was invalid.",
        },
        403: {
            "description": "The client lacks the pdf.fill permission.",
        },
        413: {
            "description": "The uploaded PDF exceeds the size limit.",
        },
        415: {
            "description": "The uploaded file is not a PDF.",
        },
        422: {
            "description": "The field mapping is invalid.",
        },
    },
)
async def fill_pdf_endpoint(
    file: UploadFile = File(
        ...,
        description="AcroForm PDF document to fill",
    ),
    fields: str = Form(
        ...,
        description=(
            "JSON object mapping PDF field names to values. "
            'Example: {"FirstName":"Cory","Approved":true}'
        ),
        examples=[
            '{"FirstName":"Cory","LastName":"Funk","Approved":true}'
        ],
    ),
    flatten: bool = Form(
        False,
        description=(
            "Convert completed field appearances to regular PDF content "
            "and remove interactive form widgets."
        ),
    ),
    strict_fields: bool = Form(
        True,
        description=(
            "Reject the request when the mapping contains field names that "
            "do not exist in the uploaded PDF."
        ),
    ),
    client: AuthenticatedClient = Depends(
        require_permission("pdf.fill")
    ),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """Fill a PDF form and return the completed PDF."""

    del client

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
        parsed_mapping = parse_field_mapping(fields, settings)
    except InvalidFieldMappingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    try:
        output_pdf, fields_applied, unknown_fields_ignored = fill_pdf_form(
            pdf_data,
            parsed_mapping.fields,
            flatten=flatten,
            strict_fields=strict_fields,
        )
    except UnknownFormFieldsError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except EncryptedPDFError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except MissingFormFieldsError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except InvalidPDFFormError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    response_headers = {
        "Content-Disposition": 'attachment; filename="filled.pdf"',
        "Cache-Control": "no-store",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
        "X-PDF-Fields-Applied": str(fields_applied),
        "X-PDF-Unknown-Fields-Ignored": str(unknown_fields_ignored),
        "X-PDF-Flattened": str(flatten).lower(),
    }

    return StreamingResponse(
        BytesIO(output_pdf),
        media_type="application/pdf",
        headers=response_headers,
    )
