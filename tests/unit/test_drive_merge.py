"""
Unit tests for Google Drive PDF merge orchestration.
"""

from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter

from app.clients.google_drive import (
    GOOGLE_DRIVE_FOLDER_MIME_TYPE,
    PDF_MIME_TYPE,
    GoogleDriveFile,
)
from app.services.drive import (
    DriveOutputExistsError,
    InvalidDrivePDFError,
    merge_drive_pdfs,
)


def create_pdf(
    width: float,
    height: float,
) -> bytes:
    """Create one in-memory PDF page."""

    writer = PdfWriter()
    writer.add_blank_page(width=width, height=height)

    output = BytesIO()
    writer.write(output)

    return output.getvalue()


class FakeDriveClient:
    """In-memory Drive client used by workflow tests."""

    def __init__(
        self,
        *,
        files: dict[str, tuple[GoogleDriveFile, bytes]],
        existing: list[GoogleDriveFile] | None = None,
    ) -> None:
        self.files = files
        self.existing = existing or []
        self.uploaded_data: bytes | None = None
        self.uploaded_name: str | None = None
        self.trashed_ids: list[str] = []

    async def get_file_metadata(
        self,
        file_id: str,
    ) -> GoogleDriveFile:
        """Return fake metadata."""

        if file_id == "destination":
            return GoogleDriveFile(
                id="destination",
                name="Packets",
                mime_type=GOOGLE_DRIVE_FOLDER_MIME_TYPE,
                size=None,
                trashed=False,
            )

        return self.files[file_id][0]

    async def find_files_by_exact_name(
        self,
        *,
        folder_id: str,
        name: str,
    ) -> list[GoogleDriveFile]:
        """Return configured exact-name files."""

        assert folder_id == "destination"
        return self.existing

    async def download_file(
        self,
        file_id: str,
        *,
        maximum_bytes: int,
    ) -> bytes:
        """Return fake PDF bytes."""

        data = self.files[file_id][1]
        assert len(data) <= maximum_bytes
        return data

    async def upload_pdf(
        self,
        *,
        folder_id: str,
        output_name: str,
        pdf_data: bytes,
    ) -> GoogleDriveFile:
        """Capture uploaded output."""

        assert folder_id == "destination"

        self.uploaded_data = pdf_data
        self.uploaded_name = output_name

        return GoogleDriveFile(
            id="new-file",
            name=output_name,
            mime_type=PDF_MIME_TYPE,
            size=len(pdf_data),
            trashed=False,
        )

    async def move_file_to_trash(
        self,
        file_id: str,
    ) -> None:
        """Record trash operations."""

        self.trashed_ids.append(file_id)


@pytest.mark.anyio
async def test_drive_merge_preserves_source_order() -> None:
    """Verify source files are merged in the requested order."""

    first = create_pdf(100, 200)
    second = create_pdf(300, 400)

    drive = FakeDriveClient(
        files={
            "first": (
                GoogleDriveFile(
                    id="first",
                    name="First.pdf",
                    mime_type=PDF_MIME_TYPE,
                    size=len(first),
                    trashed=False,
                ),
                first,
            ),
            "second": (
                GoogleDriveFile(
                    id="second",
                    name="Second.pdf",
                    mime_type=PDF_MIME_TYPE,
                    size=len(second),
                    trashed=False,
                ),
                second,
            ),
        }
    )

    result = await merge_drive_pdfs(
        drive_client=drive,
        source_file_ids=["first", "second"],
        destination_folder_id="destination",
        output_name="League Packet",
        overwrite_existing=False,
        maximum_files=50,
        maximum_bytes=10_000_000,
    )

    assert result.file_id == "new-file"
    assert result.page_count == 2
    assert result.source_file_count == 2
    assert result.replaced_file_count == 0
    assert drive.uploaded_name == "League_Packet.pdf"
    assert drive.uploaded_data is not None

    reader = PdfReader(BytesIO(drive.uploaded_data))

    assert float(reader.pages[0].mediabox.width) == 100.0
    assert float(reader.pages[1].mediabox.width) == 300.0


@pytest.mark.anyio
async def test_existing_output_requires_overwrite() -> None:
    """Verify an existing exact-name file produces a conflict."""

    document = create_pdf(100, 200)

    existing = GoogleDriveFile(
        id="existing",
        name="Packet.pdf",
        mime_type=PDF_MIME_TYPE,
        size=100,
        trashed=False,
    )

    drive = FakeDriveClient(
        files={
            "one": (
                GoogleDriveFile(
                    id="one",
                    name="One.pdf",
                    mime_type=PDF_MIME_TYPE,
                    size=len(document),
                    trashed=False,
                ),
                document,
            ),
            "two": (
                GoogleDriveFile(
                    id="two",
                    name="Two.pdf",
                    mime_type=PDF_MIME_TYPE,
                    size=len(document),
                    trashed=False,
                ),
                document,
            ),
        },
        existing=[existing],
    )

    with pytest.raises(DriveOutputExistsError):
        await merge_drive_pdfs(
            drive_client=drive,
            source_file_ids=["one", "two"],
            destination_folder_id="destination",
            output_name="Packet.pdf",
            overwrite_existing=False,
            maximum_files=50,
            maximum_bytes=10_000_000,
        )

    assert drive.uploaded_data is None
    assert drive.trashed_ids == []


@pytest.mark.anyio
async def test_overwrite_uploads_before_trashing_existing() -> None:
    """Verify overwrite replaces exact-name files after successful upload."""

    document = create_pdf(100, 200)

    existing = GoogleDriveFile(
        id="existing",
        name="Packet.pdf",
        mime_type=PDF_MIME_TYPE,
        size=100,
        trashed=False,
    )

    drive = FakeDriveClient(
        files={
            "one": (
                GoogleDriveFile(
                    id="one",
                    name="One.pdf",
                    mime_type=PDF_MIME_TYPE,
                    size=len(document),
                    trashed=False,
                ),
                document,
            ),
            "two": (
                GoogleDriveFile(
                    id="two",
                    name="Two.pdf",
                    mime_type=PDF_MIME_TYPE,
                    size=len(document),
                    trashed=False,
                ),
                document,
            ),
        },
        existing=[existing],
    )

    result = await merge_drive_pdfs(
        drive_client=drive,
        source_file_ids=["one", "two"],
        destination_folder_id="destination",
        output_name="Packet.pdf",
        overwrite_existing=True,
        maximum_files=50,
        maximum_bytes=10_000_000,
    )

    assert result.replaced_file_count == 1
    assert drive.uploaded_data is not None
    assert drive.trashed_ids == ["existing"]


@pytest.mark.anyio
async def test_non_pdf_drive_source_is_rejected() -> None:
    """Verify native or non-PDF Drive files are rejected."""

    document = create_pdf(100, 200)

    drive = FakeDriveClient(
        files={
            "one": (
                GoogleDriveFile(
                    id="one",
                    name="One.pdf",
                    mime_type=PDF_MIME_TYPE,
                    size=len(document),
                    trashed=False,
                ),
                document,
            ),
            "two": (
                GoogleDriveFile(
                    id="two",
                    name="Document",
                    mime_type="application/vnd.google-apps.document",
                    size=None,
                    trashed=False,
                ),
                b"",
            ),
        }
    )

    with pytest.raises(InvalidDrivePDFError):
        await merge_drive_pdfs(
            drive_client=drive,
            source_file_ids=["one", "two"],
            destination_folder_id="destination",
            output_name="Packet.pdf",
            overwrite_existing=False,
            maximum_files=50,
            maximum_bytes=10_000_000,
        )
