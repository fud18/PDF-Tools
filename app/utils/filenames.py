"""
Filename normalization helpers.

Drive filenames and HTTP Content-Disposition filenames have different safety
requirements. Google Drive supports spaces, commas, ampersands, parentheses,
and most printable characters, while HTTP response headers require stricter
sanitization.
"""

from __future__ import annotations

import re


def sanitize_drive_output_name(output_name: str) -> str:
    """
    Return a safe Google Drive PDF filename while preserving valid characters.

    Control characters are removed, path separators are replaced, surrounding
    whitespace is trimmed, and a PDF extension is added when missing.
    """

    candidate = output_name.strip()
    candidate = re.sub(r"[\x00-\x1f\x7f]", "", candidate)
    candidate = candidate.replace("/", "-")
    candidate = candidate.replace("\\", "-")

    if not candidate:
        raise ValueError("The output filename cannot be empty.")

    if not candidate.lower().endswith(".pdf"):
        candidate += ".pdf"

    return candidate
