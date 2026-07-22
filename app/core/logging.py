import json
import logging
import re
from datetime import UTC, datetime
from typing import Any


_SENSITIVE_VALUE_PATTERN = re.compile(
    r'(["\']?\b(?:signaturevalue|access_token|refresh_token|client_secret|'
    r'password(?:_?[12])?|telegram_bot_token)\b["\']?\s*[:=]\s*)'
    r'(["\']?)([^&,\s"\'}]+)\2',
    flags=re.IGNORECASE,
)
_STRUCTURED_FIELDS = (
    "request_id",
    "correlation_id",
    "method",
    "path",
    "status_code",
    "response_time_ms",
)


def redact_sensitive(value: str) -> str:
    """Mask known credentials and callback signatures in log text."""

    return _SENSITIVE_VALUE_PATTERN.sub(
        lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]{match.group(2)}",
        value,
    )


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive(record.getMessage()),
        }
        for field in _STRUCTURED_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exception"] = redact_sensitive(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
