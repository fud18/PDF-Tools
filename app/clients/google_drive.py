"""
Asynchronous Google Drive API client.

The supplied OAuth access token is retained only for the lifetime of the
request-scoped client. It is not persisted or intentionally logged.
"""

import json
import uuid
from dataclasses import dataclass

import httpx

GOOGLE_DRIVE_FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
PDF_MIME_TYPE = "application/pdf"


class GoogleDriveClientError(RuntimeError):
    """Base exception for delegated Google Drive operations."""


class GoogleDriveAuthenticationError(GoogleDriveClientError):
    """Raised when Google rejects the OAuth access token."""


class GoogleDrivePermissionError(GoogleDriveClientError):
    """Raised when the effective user lacks Drive permission."""


class GoogleDriveNotFoundError(GoogleDriveClientError):
    """Raised when a Drive file or folder cannot be found."""


class GoogleDriveRequestError(GoogleDriveClientError):
    """Raised when Google Drive returns another unsuccessful response."""


class GoogleDriveDownloadLimitError(GoogleDriveClientError):
    """Raised when a downloaded file exceeds its remaining byte allowance."""


@dataclass(frozen=True)
class GoogleDriveFile:
    """Selected Google Drive file metadata."""

    id: str
    name: str
    mime_type: str
    size: int | None
    trashed: bool


class GoogleDriveClient:
    """Minimal asynchronous client for Google Drive API v3."""

    def __init__(
        self,
        *,
        oauth_token: str,
        api_base_url: str,
        upload_base_url: str,
        timeout_seconds: float,
    ) -> None:
        self._api_base_url = api_base_url.rstrip("/")
        self._upload_base_url = upload_base_url.rstrip("/")

        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {oauth_token}",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
        )

    async def __aenter__(self) -> "GoogleDriveClient":
        """Enter the asynchronous client context."""

        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc: object,
        traceback: object,
    ) -> None:
        """Close the underlying HTTP client."""

        await self.aclose()

    async def aclose(self) -> None:
        """Close network resources."""

        await self._client.aclose()

    async def _raise_for_drive_error(
        self,
        response: httpx.Response,
        *,
        operation: str,
    ) -> None:
        """Map Google Drive failures to sanitized client exceptions."""

        if response.is_success:
            return

        message = f"Google Drive could not complete the {operation} operation."

        if response.status_code == 401:
            raise GoogleDriveAuthenticationError(
                "The delegated Google OAuth token is invalid or expired."
            )

        if response.status_code == 403:
            raise GoogleDrivePermissionError(
                "The effective Google user is not authorized for the requested " "Drive operation."
            )

        if response.status_code == 404:
            raise GoogleDriveNotFoundError(
                "The requested Google Drive file or folder was not found."
            )

        raise GoogleDriveRequestError(f"{message} Google returned HTTP {response.status_code}.")

    async def get_file_metadata(
        self,
        file_id: str,
    ) -> GoogleDriveFile:
        """Return selected metadata for one Drive item."""

        response = await self._client.get(
            f"{self._api_base_url}/files/{file_id}",
            params={
                "fields": "id,name,mimeType,size,trashed",
                "supportsAllDrives": "true",
            },
        )

        await self._raise_for_drive_error(
            response,
            operation="file metadata",
        )

        payload = response.json()

        raw_size = payload.get("size")

        return GoogleDriveFile(
            id=str(payload["id"]),
            name=str(payload.get("name", "")),
            mime_type=str(payload.get("mimeType", "")),
            size=int(raw_size) if raw_size is not None else None,
            trashed=bool(payload.get("trashed", False)),
        )

    async def download_file(
        self,
        file_id: str,
        *,
        maximum_bytes: int,
    ) -> bytes:
        """Download a stored Drive file with an enforced byte limit."""

        chunks: list[bytes] = []
        downloaded_bytes = 0

        async with self._client.stream(
            "GET",
            f"{self._api_base_url}/files/{file_id}",
            params={
                "alt": "media",
                "supportsAllDrives": "true",
            },
            headers={
                "Accept": "application/pdf",
            },
        ) as response:
            await self._raise_for_drive_error(
                response,
                operation="file download",
            )

            async for chunk in response.aiter_bytes():
                downloaded_bytes += len(chunk)

                if downloaded_bytes > maximum_bytes:
                    raise GoogleDriveDownloadLimitError(
                        "The Drive PDF exceeds the remaining merge-size limit."
                    )

                chunks.append(chunk)

        return b"".join(chunks)

    @staticmethod
    def _escape_drive_query_value(value: str) -> str:
        """Escape a string literal for a Drive API query."""

        return value.replace("\\", "\\\\").replace("'", "\\'")

    async def find_files_by_exact_name(
        self,
        *,
        folder_id: str,
        name: str,
    ) -> list[GoogleDriveFile]:
        """Find non-trashed exact-name files in a destination folder."""

        escaped_folder_id = self._escape_drive_query_value(folder_id)
        escaped_name = self._escape_drive_query_value(name)

        query = (
            f"'{escaped_folder_id}' in parents and " f"name = '{escaped_name}' and trashed = false"
        )

        results: list[GoogleDriveFile] = []
        page_token: str | None = None

        while True:
            params: dict[str, str] = {
                "q": query,
                "fields": ("nextPageToken," "files(id,name,mimeType,size,trashed)"),
                "pageSize": "1000",
                "spaces": "drive",
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            }

            if page_token:
                params["pageToken"] = page_token

            response = await self._client.get(
                f"{self._api_base_url}/files",
                params=params,
            )

            await self._raise_for_drive_error(
                response,
                operation="file search",
            )

            payload = response.json()

            for item in payload.get("files", []):
                raw_size = item.get("size")

                results.append(
                    GoogleDriveFile(
                        id=str(item["id"]),
                        name=str(item.get("name", "")),
                        mime_type=str(item.get("mimeType", "")),
                        size=(int(raw_size) if raw_size is not None else None),
                        trashed=bool(item.get("trashed", False)),
                    )
                )

            page_token = payload.get("nextPageToken")

            if not page_token:
                break

        return results

    async def upload_pdf(
        self,
        *,
        folder_id: str,
        output_name: str,
        pdf_data: bytes,
    ) -> GoogleDriveFile:
        """Upload a PDF using a Drive multipart/related request."""

        boundary = f"pdf-tools-{uuid.uuid4().hex}"

        metadata = json.dumps(
            {
                "name": output_name,
                "mimeType": PDF_MIME_TYPE,
                "parents": [folder_id],
            },
            separators=(",", ":"),
        ).encode("utf-8")

        body = b"".join(
            [
                f"--{boundary}\r\n".encode(),
                b"Content-Type: application/json; charset=UTF-8\r\n\r\n",
                metadata,
                b"\r\n",
                f"--{boundary}\r\n".encode(),
                b"Content-Type: application/pdf\r\n\r\n",
                pdf_data,
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            ]
        )

        response = await self._client.post(
            f"{self._upload_base_url}/files",
            params={
                "uploadType": "multipart",
                "supportsAllDrives": "true",
                "fields": "id,name,mimeType,size,trashed",
            },
            content=body,
            headers={
                "Content-Type": (f"multipart/related; boundary={boundary}"),
                "Accept": "application/json",
            },
        )

        await self._raise_for_drive_error(
            response,
            operation="file upload",
        )

        payload = response.json()
        raw_size = payload.get("size")

        return GoogleDriveFile(
            id=str(payload["id"]),
            name=str(payload.get("name", output_name)),
            mime_type=str(payload.get("mimeType", PDF_MIME_TYPE)),
            size=int(raw_size) if raw_size is not None else len(pdf_data),
            trashed=bool(payload.get("trashed", False)),
        )

    async def move_file_to_trash(
        self,
        file_id: str,
    ) -> None:
        """Move one Drive file to trash."""

        response = await self._client.patch(
            f"{self._api_base_url}/files/{file_id}",
            params={
                "supportsAllDrives": "true",
                "fields": "id,trashed",
            },
            json={
                "trashed": True,
            },
        )

        await self._raise_for_drive_error(
            response,
            operation="file trash",
        )
