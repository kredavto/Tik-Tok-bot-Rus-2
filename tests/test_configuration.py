import pytest

from app.core.config import validate_runtime_settings
from app.services.configuration import (
    is_secret_like,
    validate_runtime_configuration,
    validate_setting_value,
)


def test_secret_like_keys_are_detected() -> None:
    assert is_secret_like("TIKTOK_CLIENT_SECRET")
    assert is_secret_like("ROBOKASSA_PASSWORD_1")
    assert is_secret_like("TOKEN_ENCRYPTION_KEY")
    assert not is_secret_like("intake_enabled")


def test_configuration_import_rejects_secret_settings() -> None:
    payload = {
        "version": 1,
        "plans": [],
        "system_settings": [{"key": "ADMIN_API_TOKEN", "value": "secret"}],
    }

    with pytest.raises(ValueError):
        validate_runtime_configuration(payload)


def test_configuration_import_accepts_non_secret_settings() -> None:
    payload = {
        "version": 1,
        "plans": [
            {
                "id": "pro",
                "title": "PRO",
                "price_rub": 499,
                "price_stars": 250,
                "daily_limit": 5,
            }
        ],
        "system_settings": [{"key": "intake_enabled", "value": "true"}],
    }

    validate_runtime_configuration(payload)


def test_configuration_import_rejects_non_positive_stars_price() -> None:
    payload = {
        "version": 1,
        "plans": [
            {
                "id": "pro",
                "title": "PRO",
                "price_rub": 499,
                "price_stars": 0,
                "daily_limit": 5,
            }
        ],
        "system_settings": [],
    }

    with pytest.raises(ValueError, match="Stars"):
        validate_runtime_configuration(payload)


@pytest.mark.parametrize(
    ("value", "value_type"),
    [("48", "int"), ("false", "bool"), ('{"enabled": true}', "json")],
)
def test_typed_system_setting_accepts_valid_value(value: str, value_type: str) -> None:
    validate_setting_value(value, value_type)


@pytest.mark.parametrize(
    ("value", "value_type"),
    [("many", "int"), ("yes", "bool"), ("{", "json"), ("value", "secret")],
)
def test_typed_system_setting_rejects_invalid_value(value: str, value_type: str) -> None:
    with pytest.raises((ValueError, TypeError)):
        validate_setting_value(value, value_type)


def test_webhook_mode_requires_https_and_secret(monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "telegram_delivery_mode", "webhook")
    monkeypatch.setattr(settings, "bot_token", "test-token")
    monkeypatch.setattr(settings, "telegram_webhook_secret", "webhook-secret")
    monkeypatch.setattr(settings, "public_base_url", "http://example.com")

    with pytest.raises(RuntimeError, match="HTTPS"):
        validate_runtime_settings()

    monkeypatch.setattr(settings, "public_base_url", "https://example.com")
    validate_runtime_settings()
