"""
Request and result models for delegated Google Drive PDF merging.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PDFMergeDriveRequest(BaseModel):
    """Request to merge Drive-hosted PDF documents."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "files": [
                        "1RegistrationPdfFileId",
                        "1WaiverPdfFileId",
                        "1InsurancePdfFileId",
                    ],
                    "destination_folder_id": "1PacketDestinationFolderId",
                    "output_name": ("25 Russell Jr Broncos - Funk, Cory Packet.pdf"),
                    "overwrite_existing": False,
                }
            ]
        },
    )

    files: list[str] = Field(
        ...,
        min_length=2,
        description=("Google Drive PDF file IDs in the exact order they should be " "merged."),
    )
    destination_folder_id: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="Google Drive destination folder ID.",
    )
    output_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Filename for the completed PDF packet.",
    )
    overwrite_existing: bool = Field(
        False,
        description=(
            "Upload the new packet and move existing exact-name files to "
            "Drive trash after the upload succeeds."
        ),
    )

    @field_validator("files")
    @classmethod
    def validate_file_ids(cls, values: list[str]) -> list[str]:
        """Normalize and validate Drive file IDs."""

        normalized = [value.strip() for value in values]

        if any(not value for value in normalized):
            raise ValueError("Drive file IDs cannot be empty.")

        if len(set(normalized)) != len(normalized):
            raise ValueError("Duplicate Drive file IDs are not allowed.")

        return normalized

    @field_validator("destination_folder_id")
    @classmethod
    def normalize_folder_id(cls, value: str) -> str:
        """Normalize the destination folder ID."""

        normalized = value.strip()

        if not normalized:
            raise ValueError("The destination folder ID cannot be empty.")

        return normalized

    @field_validator("output_name")
    @classmethod
    def normalize_output_name(cls, value: str) -> str:
        """Normalize the requested output filename."""

        normalized = value.strip()

        if not normalized:
            raise ValueError("The output filename cannot be empty.")

        return normalized


class PDFMergeDriveResult(BaseModel):
    """Result returned after a successful Drive merge operation."""

    file_id: str
    name: str
    url: str
    size: int
    page_count: int
    source_file_count: int
    replaced_file_count: int
