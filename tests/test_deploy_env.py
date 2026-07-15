import base64
from pathlib import Path

import pytest

from app.core.deploy_validation import parse_env_file, validate_environment


def valid_environment() -> dict[str, str]:
    return {
        "APP_ENV": "production",
        "PUBLIC_BASE_URL": "https://loader.example.net",
        "DOMAIN": "loader.example.net",
        "NGINX_TEMPLATE": "https.conf.template",
        "TLS_CERT_DIR": "./deploy/nginx/certs",
        "APP_IMAGE": "tik-tok-loader",
        "TELEGRAM_DELIVERY_MODE": "webhook",
        "TELEGRAM_BOT_TOKEN": "12345678" + ":" + "A" * 35,
        "TELEGRAM_WEBHOOK_SECRET": "telegram-" + "a" * 32,
        "TELEGRAM_WEBHOOK_PATH": "/api/v1/webhooks/telegram",
        "TELEGRAM_WEBHOOK_CHECK_SECONDS": "300",
        "TELEGRAM_ADMIN_IDS": "123456789,987654321",
        "DATABASE_URL": "postgresql+asyncpg://app:password@postgres:5432/loader",
        "POSTGRES_DB": "loader",
        "POSTGRES_USER": "app",
        "POSTGRES_PASSWORD": "postgres-" + "b" * 24,
        "REDIS_URL": "redis://redis:6379/0",
        "TOKEN_ENCRYPTION_KEY": base64.urlsafe_b64encode(b"k" * 32).decode(),
        "ADMIN_API_TOKEN": "admin-api-" + "c" * 32,
        "ADMIN_CSRF_TOKEN": "admin-csrf-" + "d" * 32,
        "ROBOKASSA_MERCHANT_LOGIN": "merchant",
        "ROBOKASSA_PASSWORD_1": "robokassa-one-" + "e" * 20,
        "ROBOKASSA_PASSWORD_2": "robokassa-two-" + "f" * 20,
        "ROBOKASSA_RESULT_URL": "https://loader.example.net/api/v1/payments/robokassa/result",
        "ROBOKASSA_SUCCESS_URL": "https://loader.example.net/api/v1/payments/robokassa/success",
        "ROBOKASSA_FAIL_URL": "https://loader.example.net/api/v1/payments/robokassa/fail",
        "ROBOKASSA_TEST_MODE": "false",
        "ROBOKASSA_HASH_ALGORITHM": "sha256",  # pragma: allowlist secret
        "TIKTOK_PUBLISH_ENABLED": "false",
    }


def test_valid_production_environment_passes() -> None:
    result = validate_environment(valid_environment(), "production")
    assert result.is_valid


def test_placeholder_and_insecure_callback_are_rejected() -> None:
    values = valid_environment()
    values["POSTGRES_PASSWORD"] = "replace_me"
    values["ROBOKASSA_RESULT_URL"] = "http://loader.example.net/result"

    result = validate_environment(values, "production")

    assert not result.is_valid
    assert any(error.startswith("POSTGRES_PASSWORD:") for error in result.errors)
    assert any(error.startswith("ROBOKASSA_RESULT_URL:") for error in result.errors)


def test_tiktok_credentials_are_required_only_when_publishing_is_enabled() -> None:
    values = valid_environment()
    values["TIKTOK_PUBLISH_ENABLED"] = "true"

    result = validate_environment(values, "production")

    assert any(error.startswith("TIKTOK_CLIENT_KEY:") for error in result.errors)
    assert any(error.startswith("TIKTOK_CLIENT_SECRET:") for error in result.errors)


def test_duplicate_secret_values_are_rejected() -> None:
    values = valid_environment()
    values["ADMIN_CSRF_TOKEN"] = values["ADMIN_API_TOKEN"]

    result = validate_environment(values, "production")

    assert "SECRET_VALUES: each configured secret must be unique" in result.errors


def test_production_rejects_robokassa_test_mode() -> None:
    values = valid_environment()
    values["ROBOKASSA_TEST_MODE"] = "true"

    result = validate_environment(values, "production")

    assert "ROBOKASSA_TEST_MODE: production requires false" in result.errors


def test_invalid_robokassa_hash_algorithm_is_rejected() -> None:
    values = valid_environment()
    values["ROBOKASSA_HASH_ALGORITHM"] = "sha1"

    result = validate_environment(values, "production")

    assert "ROBOKASSA_HASH_ALGORITHM: must be md5, sha256, or sha512" in result.errors


def test_callback_paths_must_match_the_public_contract() -> None:
    values = valid_environment()
    values["ROBOKASSA_RESULT_URL"] = "https://loader.example.net/result"

    result = validate_environment(values, "production")

    assert any(error.startswith("ROBOKASSA_RESULT_URL: must be") for error in result.errors)


def test_tiktok_callback_must_match_when_publishing_is_enabled() -> None:
    values = valid_environment()
    values.update(
        {
            "TIKTOK_PUBLISH_ENABLED": "true",
            "TIKTOK_CLIENT_KEY": "client-key",  # pragma: allowlist secret
            "TIKTOK_CLIENT_SECRET": "tiktok-client-" + "g" * 20,  # pragma: allowlist secret
            "TIKTOK_WEBHOOK_SECRET": "tiktok-webhook-" + "h" * 20,  # pragma: allowlist secret
            "TIKTOK_REDIRECT_URI": "https://loader.example.net/wrong-callback",
        }
    )

    result = validate_environment(values, "production")

    assert any(error.startswith("TIKTOK_REDIRECT_URI: must be") for error in result.errors)


def test_env_parser_rejects_duplicate_variables(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=production\nAPP_ENV=staging\n")

    with pytest.raises(ValueError, match="duplicate variable"):
        parse_env_file(env_file)
