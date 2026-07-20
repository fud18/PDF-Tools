"""
PDF Tools application configuration.

Runtime settings are loaded from environment variables. Secrets and
environment-specific configuration remain outside the Git repository.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the PDF Tools service."""

    app_name: str = "PDF Tools"
    app_version: str = "0.6.0"
    environment: str = "production"

    clients_file: str = "/etc/pdf-tools/clients.json"

    max_upload_bytes: int = 104_857_600
    max_merge_files: int = 50
    max_merge_request_bytes: int = 209_715_200

    drive_api_base_url: str = "https://www.googleapis.com/drive/v3"
    drive_upload_base_url: str = "https://www.googleapis.com/upload/drive/v3"
    drive_request_timeout_seconds: float = 120.0
    max_drive_merge_files: int = 50
    max_drive_merge_bytes: int = 524_288_000

    max_field_mapping_bytes: int = 1_048_576
    max_form_fields: int = 1_000
    max_field_name_length: int = 512
    max_field_value_length: int = 32_768

    log_level: str = "INFO"
    worker_count: int = 2

    model_config = SettingsConfigDict(
        env_prefix="PDFTOOLS_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()
