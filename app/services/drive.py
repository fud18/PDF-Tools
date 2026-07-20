"""
Google Drive PDF merge orchestration.

This service verifies Drive resources, downloads PDF documents, merges them in
the requested order, uploads the completed packet, and optionally trashes
existing exact-name output files after the new upload succeeds.
"""

from dataclasses import dataclass

from app.clients.google_drive import (
    GOOGLE_DRIVE_FOLDER_MIME_TYPE,
    PDF_MIME_TYPE,
    GoogleDriveClient,
    GoogleDriveDownloadLimitError,
)
from app.services.pdf_merge import (
    PDFMergeError,
    merge_pdf_documents,
    sanitize_output_name,
)


class DriveMergeError(RuntimeError):
    """Base exception for Drive merge workflows."""


class InvalidDriveFolderError(DriveMergeError):
    """Raised when the destination is not an accessible Drive folder."""


class InvalidDrivePDFError(DriveMergeError):
    """Raised when a source is not a supported Drive-hosted PDF."""


class DriveMergeTooLargeError(DriveMergeError):
    """Raised when source PDFs exceed the aggregate merge limit."""


class DriveOutputExistsError(DriveMergeError):
    """Raised when output exists and overwrite was not requested."""

    def __init__(self, existing_count: int) -> None:
        super().__init__(
            "A file with the requested output name already exists in the " "destination folder."
        )
        self.existing_count = existing_count


@dataclass(frozen=True)
class DriveMergeResult:
    """Completed Drive merge information."""

    file_id: str
    name: str
    url: str
    size: int
    page_count: int
    source_file_count: int
    replaced_file_count: int


async def merge_drive_pdfs(
    *,
    drive_client: GoogleDriveClient,
    source_file_ids: list[str],
    destination_folder_id: str,
    output_name: str,
    overwrite_existing: bool,
    maximum_files: int,
    maximum_bytes: int,
) -> DriveMergeResult:
    """
    Merge Drive-hosted PDFs and upload the resulting packet.

    Existing matching files are moved to trash only after the replacement
    upload succeeds.
    """

    if len(source_file_ids) < 2:
        raise DriveMergeError("At least two Drive PDF files are required.")

    if len(source_file_ids) > maximum_files:
        raise DriveMergeError("The request contains more Drive files than the configured limit.")

    safe_output_name = sanitize_output_name(output_name)

    folder = await drive_client.get_file_metadata(destination_folder_id)

    if folder.trashed or folder.mime_type != GOOGLE_DRIVE_FOLDER_MIME_TYPE:
        raise InvalidDriveFolderError("The destination Drive item is not an active folder.")

    existing_files = await drive_client.find_files_by_exact_name(
        folder_id=destination_folder_id,
        name=safe_output_name,
    )

    if existing_files and not overwrite_existing:
        raise DriveOutputExistsError(len(existing_files))

    pdf_documents: list[bytes] = []
    total_input_bytes = 0

    for position, file_id in enumerate(source_file_ids, start=1):
        metadata = await drive_client.get_file_metadata(file_id)

        if metadata.trashed:
            raise InvalidDrivePDFError(f"Drive source file number {position} is in trash.")

        if metadata.mime_type != PDF_MIME_TYPE:
            raise InvalidDrivePDFError(f"Drive source file number {position} is not a PDF.")

        if metadata.size is not None and total_input_bytes + metadata.size > maximum_bytes:
            raise DriveMergeTooLargeError(
                "The Drive PDFs exceed the configured aggregate size limit."
            )

        remaining_bytes = maximum_bytes - total_input_bytes

        try:
            pdf_data = await drive_client.download_file(
                file_id,
                maximum_bytes=remaining_bytes,
            )
        except GoogleDriveDownloadLimitError as exc:
            raise DriveMergeTooLargeError(str(exc)) from exc

        if not pdf_data.startswith(b"%PDF-"):
            raise InvalidDrivePDFError(
                f"Drive source file number {position} does not contain a " "valid PDF header."
            )

        total_input_bytes += len(pdf_data)
        pdf_documents.append(pdf_data)

    try:
        merged_pdf, page_count = merge_pdf_documents(pdf_documents)
    except PDFMergeError as exc:
        raise DriveMergeError(str(exc)) from exc

    uploaded_file = await drive_client.upload_pdf(
        folder_id=destination_folder_id,
        output_name=safe_output_name,
        pdf_data=merged_pdf,
    )

    replaced_file_count = 0

    if overwrite_existing:
        for existing_file in existing_files:
            if existing_file.id == uploaded_file.id:
                continue

            await drive_client.move_file_to_trash(existing_file.id)
            replaced_file_count += 1

    return DriveMergeResult(
        file_id=uploaded_file.id,
        name=uploaded_file.name,
        url=("https://drive.google.com/file/d/" f"{uploaded_file.id}/view"),
        size=uploaded_file.size or len(merged_pdf),
        page_count=page_count,
        source_file_count=len(source_file_ids),
        replaced_file_count=replaced_file_count,
    )
