"""
Stable PDF Tools application error codes.

Error-code ranges:

PDFT-1000 through PDFT-1099: request validation
PDFT-1100 through PDFT-1199: authentication and authorization
PDFT-1200 through PDFT-1299: PDF processing
PDFT-1300 through PDFT-1399: file uploads
PDFT-1400 through PDFT-1499: configuration
PDFT-1500 through PDFT-1599: unexpected server errors
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Stable machine-readable API error codes."""

    VALIDATION_ERROR = "PDFT-1000"
    UNKNOWN_FORM_FIELD = "PDFT-1001"
    INVALID_FIELD_MAPPING = "PDFT-1002"

    AUTHENTICATION_REQUIRED = "PDFT-1100"
    INVALID_API_KEY = "PDFT-1101"
    PERMISSION_DENIED = "PDFT-1102"

    PDF_PROCESSING_ERROR = "PDFT-1200"
    INVALID_PDF = "PDFT-1201"
    ENCRYPTED_PDF = "PDFT-1202"
    MISSING_FORM_FIELDS = "PDFT-1203"

    FILE_UPLOAD_ERROR = "PDFT-1300"
    FILE_TOO_LARGE = "PDFT-1301"
    UNSUPPORTED_MEDIA_TYPE = "PDFT-1302"

    CONFIGURATION_ERROR = "PDFT-1400"
    AUTHENTICATION_CONFIGURATION_ERROR = "PDFT-1401"

    INTERNAL_ERROR = "PDFT-1500"
