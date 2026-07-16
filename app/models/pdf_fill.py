"""
Models and validation helpers for PDF form filling.

Field mappings are supplied as JSON in a multipart/form-data request. Only
scalar field values are accepted. Nested objects and arrays are rejected.
"""

import json
from dataclasses import dataclass

from app.core.configuration import Settings

type FieldValue = str | int | float | bool | None


@dataclass(frozen=True)
class ParsedFieldMapping:
    """Validated PDF form-field mapping."""

    fields: dict[str, FieldValue]
    encoded_size: int


class InvalidFieldMappingError(ValueError):
    """Raised when a field mapping is invalid."""


def parse_field_mapping(
    raw_mapping: str,
    settings: Settings,
) -> ParsedFieldMapping:
    """Parse and validate a JSON object containing PDF field values."""

    encoded_size = len(raw_mapping.encode("utf-8"))

    if encoded_size > settings.max_field_mapping_bytes:
        raise InvalidFieldMappingError("The field mapping exceeds the configured size limit.")

    try:
        document = json.loads(raw_mapping)
    except json.JSONDecodeError as exc:
        raise InvalidFieldMappingError("The fields value must contain valid JSON.") from exc

    if not isinstance(document, dict):
        raise InvalidFieldMappingError("The fields value must be a JSON object.")

    if len(document) > settings.max_form_fields:
        raise InvalidFieldMappingError("The field mapping contains too many entries.")

    validated: dict[str, FieldValue] = {}

    for raw_name, raw_value in document.items():
        if not isinstance(raw_name, str):
            raise InvalidFieldMappingError("Every PDF field name must be a string.")

        field_name = raw_name.strip()

        if not field_name:
            raise InvalidFieldMappingError("PDF field names cannot be empty.")

        if len(field_name) > settings.max_field_name_length:
            raise InvalidFieldMappingError("A PDF field name exceeds the configured length limit.")

        if isinstance(raw_value, (dict, list)):
            raise InvalidFieldMappingError("PDF field values must be scalar values.")

        if raw_value is not None and not isinstance(
            raw_value,
            (str, int, float, bool),
        ):
            raise InvalidFieldMappingError("A PDF field value has an unsupported type.")

        if isinstance(raw_value, str) and len(raw_value) > settings.max_field_value_length:
            raise InvalidFieldMappingError("A PDF field value exceeds the configured length limit.")

        validated[field_name] = raw_value

    return ParsedFieldMapping(
        fields=validated,
        encoded_size=encoded_size,
    )
