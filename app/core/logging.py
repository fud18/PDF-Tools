"""
Structured logging configuration for PDF Tools.

Logs contain operational metadata only. PDF contents, form values, filenames,
API keys, and document metadata are never intentionally logged.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_RESERVED_LOG_RECORD_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


class JSONFormatter(logging.Formatter):
    """Format log records as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Return a JSON-formatted representation of the log record."""

        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_FIELDS:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        )


def configure_logging(log_level: str) -> None:
    """Configure application and Uvicorn logging."""

    level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    for logger_name in (
        "uvicorn",
        "uvicorn.error",
    ):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True
        logger.setLevel(level)

    # Application middleware provides sanitized access logs.
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = False
    access_logger.disabled = True
