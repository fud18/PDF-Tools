"""
Delegated Google Drive PDF merge endpoint.

The endpoint accepts Drive file IDs rather than PDF bytes. A temporary OAuth
token supplied by the caller authorizes Drive downloads and upload operations.
The token and PDF contents are not intentionally logged or persisted.
"""

from fastapi import (
    APIRouter,
    Depends,
    Header,
    Request,
)

from app.clients.google_drive import (
    GoogleDriveAuthenticationError,
    GoogleDriveClient,
    GoogleDriveNotFoundError,
    GoogleDrivePermissionError,
    GoogleDriveRequestError,
)
from app.core.authentication import (
    AuthenticatedClient,
    require_permission,
)
from app.core.configuration import Settings, get_settings
from app.core.errors import ErrorCode
from app.core.exceptions import PDFToolsException
from app.core.openapi import AUTHENTICATED_ERROR_RESPONSES
from app.core.responses import ok
from app.models.pdf_merge_drive import (
    PDFMergeDriveRequest,
    PDFMergeDriveResult,
)
from app.models.response import SuccessResponse
from app.services.drive import (
    DriveMergeError,
    DriveMergeTooLargeError,
    DriveOutputExistsError,
    InvalidDriveFolderError,
    InvalidDrivePDFError,
    merge_drive_pdfs,
)

router = APIRouter(tags=["Google Drive"])


def _extract_bearer_token(
    authorization: str | None,
) -> str:
    """Extract a bearer token without retaining the original header."""

    if not authorization:
        raise PDFToolsException(
            code=ErrorCode.DRIVE_AUTHENTICATION_ERROR.value,
            message=("A delegated Google OAuth bearer token is required."),
            status_code=401,
        )

    scheme, separator, token = authorization.partition(" ")

    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise PDFToolsException(
            code=ErrorCode.DRIVE_AUTHENTICATION_ERROR.value,
            message=("The Authorization header must contain a valid Bearer token."),
            status_code=401,
        )

    return token.strip()


@router.post(
    "/merge-drive",
    summary="Merge Google Drive PDF files",
    description=(
        "Downloads Drive-hosted PDF files using the caller's temporary "
        "Google OAuth token, merges them in submitted order, and uploads the "
        "completed packet directly to the specified Drive folder. PDF bytes "
        "do not pass through Apps Script."
    ),
    response_model=SuccessResponse,
    responses={
        **AUTHENTICATED_ERROR_RESPONSES,
        409: {
            "description": (
                "An exact-name output file already exists and overwrite was " "not enabled."
            )
        },
    },
    response_description="Uploaded Google Drive packet information.",
)
async def merge_drive_endpoint(
    request: Request,
    payload: PDFMergeDriveRequest,
    authorization: str | None = Header(
        None,
        description=("Temporary Google OAuth access token using the Bearer scheme."),
    ),
    client: AuthenticatedClient = Depends(require_permission("pdf.merge-drive")),
    settings: Settings = Depends(get_settings),
) -> SuccessResponse:
    """Merge Drive PDFs and upload the completed packet."""

    oauth_token = _extract_bearer_token(authorization)

    if len(payload.files) > settings.max_drive_merge_files:
        raise PDFToolsException(
            code=ErrorCode.TOO_MANY_FILES.value,
            message=("The request contains too many Google Drive PDF files."),
            details={
                "maximum_files": settings.max_drive_merge_files,
                "submitted_files": len(payload.files),
            },
            status_code=413,
        )

    try:
        async with GoogleDriveClient(
            oauth_token=oauth_token,
            api_base_url=settings.drive_api_base_url,
            upload_base_url=settings.drive_upload_base_url,
            timeout_seconds=settings.drive_request_timeout_seconds,
        ) as drive_client:
            result = await merge_drive_pdfs(
                drive_client=drive_client,
                source_file_ids=payload.files,
                destination_folder_id=(payload.destination_folder_id),
                output_name=payload.output_name,
                overwrite_existing=payload.overwrite_existing,
                maximum_files=settings.max_drive_merge_files,
                maximum_bytes=settings.max_drive_merge_bytes,
            )
    except GoogleDriveAuthenticationError as exc:
        raise PDFToolsException(
            code=ErrorCode.DRIVE_AUTHENTICATION_ERROR.value,
            message=str(exc),
            status_code=401,
        ) from exc
    except GoogleDrivePermissionError as exc:
        raise PDFToolsException(
            code=ErrorCode.DRIVE_PERMISSION_ERROR.value,
            message=str(exc),
            status_code=403,
        ) from exc
    except GoogleDriveNotFoundError as exc:
        raise PDFToolsException(
            code=ErrorCode.DRIVE_FILE_NOT_FOUND.value,
            message=str(exc),
            status_code=404,
        ) from exc
    except GoogleDriveRequestError as exc:
        raise PDFToolsException(
            code=ErrorCode.DRIVE_API_ERROR.value,
            message=str(exc),
            status_code=502,
        ) from exc
    except DriveOutputExistsError as exc:
        raise PDFToolsException(
            code=ErrorCode.OUTPUT_FILE_EXISTS.value,
            message=str(exc),
            details={
                "existing_file_count": exc.existing_count,
            },
            status_code=409,
        ) from exc
    except InvalidDriveFolderError as exc:
        raise PDFToolsException(
            code=ErrorCode.DRIVE_INVALID_FOLDER.value,
            message=str(exc),
            status_code=422,
        ) from exc
    except InvalidDrivePDFError as exc:
        raise PDFToolsException(
            code=ErrorCode.DRIVE_INVALID_FILE_TYPE.value,
            message=str(exc),
            status_code=422,
        ) from exc
    except DriveMergeTooLargeError as exc:
        raise PDFToolsException(
            code=ErrorCode.DRIVE_FILE_TOO_LARGE.value,
            message=str(exc),
            details={
                "maximum_bytes": settings.max_drive_merge_bytes,
            },
            status_code=413,
        ) from exc
    except DriveMergeError as exc:
        raise PDFToolsException(
            code=ErrorCode.PDF_MERGE_FAILED.value,
            message=str(exc),
            status_code=400,
        ) from exc

    response_data = PDFMergeDriveResult(
        file_id=result.file_id,
        name=result.name,
        url=result.url,
        size=result.size,
        page_count=result.page_count,
        source_file_count=result.source_file_count,
        replaced_file_count=result.replaced_file_count,
    )

    return ok(
        request_id=request.state.request_id,
        data={
            "authenticated_client": client.name,
            **response_data.model_dump(),
        },
    )
