from dataclasses import dataclass

import pytest

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
        self.delete_drop_pending: bool | None = None

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

    async def delete_webhook(self, *, drop_pending_updates: bool) -> bool:
        self.delete_drop_pending = drop_pending_updates
        if self.delete_result:
            self.info.url = ""
        return self.delete_result


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
        secret_token="secret-value",
        allowed_updates=["message", "callback_query"],
    )

    assert status.actual_url == status.expected_url
    assert bot.set_call == {
        "url": status.expected_url,
        "secret_token": "secret-value",
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": False,
    }


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
            secret_token="secret-value",
            allowed_updates=["message"],
        )


async def test_delete_webhook_preserves_pending_updates() -> None:
    bot = FakeBot(url="https://loader.example.net/api/v1/webhooks/telegram")

    await delete_telegram_webhook(bot)

    assert bot.delete_drop_pending is False
    assert bot.info.url == ""
