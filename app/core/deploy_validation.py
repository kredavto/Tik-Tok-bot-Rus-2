from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
import re
from urllib.parse import urlparse


PLACEHOLDER_MARKERS = (
    "replace_me",
    "replace_with",
    "generate_with",
    "example.com",
    "your-domain",
)
SECRET_KEYS = (
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_WEBHOOK_SECRET",
    "POSTGRES_PASSWORD",
    "TIKTOK_CLIENT_SECRET",
    "TIKTOK_WEBHOOK_SECRET",
    "ROBOKASSA_PASSWORD_1",
    "ROBOKASSA_PASSWORD_2",
    "TOKEN_ENCRYPTION_KEY",
    "ADMIN_API_TOKEN",
    "ADMIN_CSRF_TOKEN",
)


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"line {line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise ValueError(f"line {line_number}: invalid variable name")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key in values:
            raise ValueError(f"line {line_number}: duplicate variable {key}")
        values[key] = value
    return values


def is_placeholder(value: str) -> bool:
    normalized = value.lower()
    return not value or any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def is_true(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def valid_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname)


def validate_environment(values: dict[str, str], environment: str) -> ValidationResult:
    errors: list[str] = []

    def require(key: str, *, secret: bool = False, minimum: int = 1) -> str:
        value = values.get(key, "")
        if is_placeholder(value):
            errors.append(f"{key}: required value is missing or is a placeholder")
            return ""
        elif secret and len(value) < minimum:
            errors.append(f"{key}: secret is shorter than {minimum} characters")
        return value

    configured_environment = require("APP_ENV")
    if configured_environment and configured_environment != environment:
        errors.append(f"APP_ENV: must be {environment}")

    public_url = require("PUBLIC_BASE_URL")
    if public_url and not valid_https_url(public_url):
        errors.append("PUBLIC_BASE_URL: HTTPS URL is required")
    public_host = urlparse(public_url).hostname if public_url else None

    domain = require("DOMAIN")
    if domain and public_host and domain != public_host:
        errors.append("DOMAIN: must match PUBLIC_BASE_URL host")
    if values.get("NGINX_TEMPLATE") != "https.conf.template":
        errors.append("NGINX_TEMPLATE: production-style deploy requires https.conf.template")
    require("TLS_CERT_DIR")
    require("APP_IMAGE")

    if values.get("TELEGRAM_DELIVERY_MODE") != "webhook":
        errors.append("TELEGRAM_DELIVERY_MODE: staging and production require webhook")
    bot_token = require("TELEGRAM_BOT_TOKEN", secret=True, minimum=35)
    if bot_token and not re.fullmatch(r"\d{8,12}:[A-Za-z0-9_-]{30,}", bot_token):
        errors.append("TELEGRAM_BOT_TOKEN: invalid token format")
    require("TELEGRAM_WEBHOOK_SECRET", secret=True, minimum=32)
    admin_ids = require("TELEGRAM_ADMIN_IDS")
    if admin_ids and not all(item.strip().isdigit() for item in admin_ids.split(",")):
        errors.append("TELEGRAM_ADMIN_IDS: expected comma-separated numeric IDs")

    database_url = require("DATABASE_URL")
    if database_url and not database_url.startswith("postgresql+asyncpg://"):
        errors.append("DATABASE_URL: postgresql+asyncpg URL is required")
    require("POSTGRES_DB")
    require("POSTGRES_USER")
    require("POSTGRES_PASSWORD", secret=True, minimum=16)
    redis_url = require("REDIS_URL")
    if redis_url and not redis_url.startswith(("redis://", "rediss://")):
        errors.append("REDIS_URL: Redis URL is required")

    encryption_key = require("TOKEN_ENCRYPTION_KEY", secret=True, minimum=43)
    if encryption_key:
        try:
            decoded_key = base64.urlsafe_b64decode(encryption_key.encode())
        except (ValueError, TypeError):
            decoded_key = b""
        if len(decoded_key) != 32:
            errors.append("TOKEN_ENCRYPTION_KEY: valid Fernet key is required")
    require("ADMIN_API_TOKEN", secret=True, minimum=32)
    require("ADMIN_CSRF_TOKEN", secret=True, minimum=32)

    require("ROBOKASSA_MERCHANT_LOGIN")
    require("ROBOKASSA_PASSWORD_1", secret=True, minimum=16)
    require("ROBOKASSA_PASSWORD_2", secret=True, minimum=16)
    for key in ("ROBOKASSA_RESULT_URL", "ROBOKASSA_SUCCESS_URL", "ROBOKASSA_FAIL_URL"):
        url = require(key)
        if url and not valid_https_url(url):
            errors.append(f"{key}: HTTPS URL is required")
        elif url and public_host and urlparse(url).hostname != public_host:
            errors.append(f"{key}: host must match PUBLIC_BASE_URL")
    if environment == "production" and is_true(values.get("ROBOKASSA_TEST_MODE", "true")):
        errors.append("ROBOKASSA_TEST_MODE: production requires false")

    if is_true(values.get("TIKTOK_PUBLISH_ENABLED", "false")):
        require("TIKTOK_CLIENT_KEY")
        require("TIKTOK_CLIENT_SECRET", secret=True, minimum=16)
        require("TIKTOK_WEBHOOK_SECRET", secret=True, minimum=16)
        redirect_uri = require("TIKTOK_REDIRECT_URI")
        if redirect_uri and not valid_https_url(redirect_uri):
            errors.append("TIKTOK_REDIRECT_URI: HTTPS URL is required")
        elif redirect_uri and public_host and urlparse(redirect_uri).hostname != public_host:
            errors.append("TIKTOK_REDIRECT_URI: host must match PUBLIC_BASE_URL")

    populated_secrets = [
        values[key] for key in SECRET_KEYS if values.get(key) and not is_placeholder(values[key])
    ]
    if len(populated_secrets) != len(set(populated_secrets)):
        errors.append("SECRET_VALUES: each configured secret must be unique")

    return ValidationResult(tuple(dict.fromkeys(errors)))
