"""
API-key authentication and authorization for PDF Tools.

Client API keys are stored as SHA-256 hashes in an external JSON file.
Plain-text API keys are never stored in the application repository.
"""

import hashlib
import json
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.core.configuration import Settings, get_settings

api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="PDFToolsAPIKey",
    description="PDF Tools client API key",
    auto_error=False,
)


@dataclass(frozen=True)
class AuthenticatedClient:
    """Authenticated API client identity and authorization permissions."""

    name: str
    permissions: tuple[str, ...]


class ClientConfigurationError(RuntimeError):
    """Raised when the client configuration cannot be loaded."""


def _hash_api_key(api_key: str) -> str:
    """Return the SHA-256 hash of an API key."""

    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def _load_clients(clients_file: str) -> list[dict[str, Any]]:
    """Load client definitions from the external JSON configuration."""

    path = Path(clients_file)

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClientConfigurationError("The API client configuration could not be loaded.") from exc

    clients = document.get("clients")

    if not isinstance(clients, list):
        raise ClientConfigurationError(
            "The API client configuration does not contain a clients list."
        )

    return clients


def require_api_key(
    provided_api_key: str | None = Security(api_key_header),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedClient:
    """Authenticate the supplied API key and return the client identity."""

    if not provided_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="An API key is required.",
        )

    supplied_hash = _hash_api_key(provided_api_key)

    try:
        clients = _load_clients(settings.clients_file)
    except ClientConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is temporarily unavailable.",
        ) from exc

    for client in clients:
        if not client.get("enabled", False):
            continue

        configured_hash = str(client.get("key_sha256", ""))

        if configured_hash and secrets.compare_digest(
            supplied_hash,
            configured_hash,
        ):
            permissions = client.get("permissions", [])

            return AuthenticatedClient(
                name=str(client.get("name", "unknown-client")),
                permissions=tuple(str(item) for item in permissions),
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="The supplied API key is invalid.",
    )


def require_permission(
    required_permission: str,
) -> Callable[..., AuthenticatedClient]:
    """
    Create a FastAPI dependency that requires a specific client permission.

    A client with the wildcard permission "*" is authorized for every
    operation.
    """

    def dependency(
        request: Request,
        client: AuthenticatedClient = Depends(require_api_key),
    ) -> AuthenticatedClient:
        """Authorize one authenticated client for the requested operation."""

        if required_permission not in client.permissions and "*" not in client.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=("The authenticated client is not authorized " "for this operation."),
            )

        request.state.authenticated_client = client.name

        return client

    return dependency
