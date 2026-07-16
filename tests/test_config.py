from app.core.config import Settings


def test_empty_optional_admin_id_uses_none_default(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_API_TELEGRAM_ID", "")

    configured = Settings(_env_file=None)

    assert configured.admin_api_telegram_id is None
