from dataclasses import dataclass
import logging

import pytest

from app.bot import main as bot_main
from app.bot import webhook as webhook_cli
from app.services.telegram_webhook import (
    TelegramWebhookError,
    build_telegram_webhook_url,
    configure_telegram_webhook,
    delete_telegram_webhook,
    verify_telegram_webhook,
)


@dataclass
class FakeWebhookInfo:
    url: str
    pending_update_count: int = 0
    last_error_message: str | None = None


class FakeBot:
    def __init__(self, *, url: str = "", set_result: bool = True, delete_result: bool = True):
        self.info = FakeWebhookInfo(url=url)
        self.set_result = set_result
        self.delete_result = delete_result
        self.set_call: dict[str, object] | None = None
        self.commands: list[object] | None = None
        self.delete_drop_pending: bool | None = None
        self.session = FakeSession()

    async def set_webhook(
        self,
        url: str,
        *,
        secret_token: str,
        allowed_updates: list[str],
        drop_pending_updates: bool,
    ) -> bool:
        self.set_call = {
            "url": url,
            "secret_token": secret_token,
            "allowed_updates": allowed_updates,
            "drop_pending_updates": drop_pending_updates,
        }
        if self.set_result:
            self.info.url = url
        return self.set_result

    async def get_webhook_info(self) -> FakeWebhookInfo:
        return self.info

    async def set_my_commands(self, commands: list[object]) -> bool:
        self.commands = commands
        return True

    async def delete_webhook(self, *, drop_pending_updates: bool) -> bool:
        self.delete_drop_pending = drop_pending_updates
        if self.delete_result:
            self.info.url = ""
        return self.delete_result


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class FakeStorage:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class FakeDispatcher:
    def __init__(self) -> None:
        self.storage = FakeStorage()

    def resolve_used_update_types(self) -> list[str]:
        return ["message", "callback_query"]


def test_build_webhook_url_normalizes_base_url() -> None:
    assert (
        build_telegram_webhook_url(
            "https://loader.example.net/",
            "/api/v1/webhooks/telegram",
        )
        == "https://loader.example.net/api/v1/webhooks/telegram"
    )


async def test_configure_webhook_is_verified_without_dropping_updates() -> None:
    bot = FakeBot()

    status = await configure_telegram_webhook(
        bot,
        expected_url="https://loader.example.net/api/v1/webhooks/telegram",
        secret_token="secret-value",  # pragma: allowlist secret
        allowed_updates=["message", "callback_query"],
    )

    assert status.actual_url == status.expected_url
    assert bot.set_call == {
        "url": status.expected_url,
        "secret_token": "secret-value",  # pragma: allowlist secret
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": False,
    }
    assert [command.command for command in bot.commands or []] == [
        "start",
        "tariffs",
        "status",
        "terms",
        "paysupport",
        "help",
    ]


async def test_verify_webhook_rejects_configuration_drift() -> None:
    bot = FakeBot(url="https://wrong.example.net/webhook")

    with pytest.raises(TelegramWebhookError, match="does not match"):
        await verify_telegram_webhook(
            bot,
            expected_url="https://loader.example.net/api/v1/webhooks/telegram",
        )


async def test_configure_webhook_rejects_telegram_failure() -> None:
    bot = FakeBot(set_result=False)

    with pytest.raises(TelegramWebhookError, match="rejected"):
        await configure_telegram_webhook(
            bot,
            expected_url="https://loader.example.net/api/v1/webhooks/telegram",
            secret_token="secret-value",  # pragma: allowlist secret
            allowed_updates=["message"],
        )


async def test_delete_webhook_preserves_pending_updates() -> None:
    bot = FakeBot(url="https://loader.example.net/api/v1/webhooks/telegram")

    await delete_telegram_webhook(bot)

    assert bot.delete_drop_pending is False
    assert bot.info.url == ""


async def test_webhook_cli_configures_and_closes_resources(monkeypatch) -> None:
    bot = FakeBot()
    dispatcher = FakeDispatcher()
    monkeypatch.setattr(webhook_cli, "Bot", lambda token: bot)
    monkeypatch.setattr(webhook_cli, "create_dispatcher", lambda: dispatcher)
    monkeypatch.setattr(webhook_cli, "require_settings", lambda *names: None)
    monkeypatch.setattr(webhook_cli, "validate_runtime_settings", lambda: None)
    monkeypatch.setattr(webhook_cli.settings, "bot_token", "test-token")
    monkeypatch.setattr(webhook_cli.settings, "telegram_webhook_secret", "test-secret")
    monkeypatch.setattr(webhook_cli.settings, "public_base_url", "https://loader.example.net")
    monkeypatch.setattr(
        webhook_cli.settings,
        "telegram_webhook_path",
        "/api/v1/webhooks/telegram",
    )

    result = await webhook_cli.run("configure")

    assert result == 0
    assert bot.set_call is not None
    assert bot.set_call["drop_pending_updates"] is False
    assert dispatcher.storage.closed is True
    assert bot.session.closed is True


async def test_webhook_cli_does_not_log_provider_url_with_token(
    monkeypatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    bot = FakeBot(url="https://loader.example.net/api/v1/webhooks/telegram")

    async def fail_get_webhook_info() -> FakeWebhookInfo:
        raise RuntimeError("https://api.telegram.org/botSECRET_TOKEN/getWebhookInfo")

    bot.get_webhook_info = fail_get_webhook_info  # type: ignore[method-assign]
    monkeypatch.setattr(webhook_cli, "Bot", lambda token: bot)
    monkeypatch.setattr(webhook_cli, "require_settings", lambda *names: None)
    monkeypatch.setattr(webhook_cli, "validate_runtime_settings", lambda: None)
    monkeypatch.setattr(webhook_cli.settings, "bot_token", "test-token")
    monkeypatch.setattr(webhook_cli.settings, "public_base_url", "https://loader.example.net")
    monkeypatch.setattr(
        webhook_cli.settings,
        "telegram_webhook_path",
        "/api/v1/webhooks/telegram",
    )

    with caplog.at_level(logging.ERROR):
        result = await webhook_cli.run("verify")

    assert result == 1
    assert "SECRET_TOKEN" not in caplog.text
    assert bot.session.closed is True


async def test_webhook_monitor_checks_without_reconfiguring(monkeypatch) -> None:
    bot = FakeBot(url="https://loader.example.net/api/v1/webhooks/telegram")
    calls = 0

    async def verify(fake_bot, *, expected_url: str):
        nonlocal calls
        calls += 1
        return await verify_telegram_webhook(fake_bot, expected_url=expected_url)

    async def stop_after_first_check(_: int) -> None:
        raise StopAsyncIteration

    monkeypatch.setattr(bot_main, "verify_telegram_webhook", verify)
    monkeypatch.setattr(bot_main.asyncio, "sleep", stop_after_first_check)
    monkeypatch.setattr(bot_main.settings, "public_base_url", "https://loader.example.net")
    monkeypatch.setattr(
        bot_main.settings,
        "telegram_webhook_path",
        "/api/v1/webhooks/telegram",
    )

    with pytest.raises(StopAsyncIteration):
        await bot_main.monitor_webhook(bot)

    assert calls == 1
    assert bot.set_call is None
