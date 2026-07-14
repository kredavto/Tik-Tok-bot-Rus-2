from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot


class TelegramWebhookError(RuntimeError):
    """Raised when Telegram reports an unexpected webhook configuration."""


@dataclass(frozen=True)
class TelegramWebhookStatus:
    expected_url: str
    actual_url: str
    pending_update_count: int
    last_error_message: str | None


def build_telegram_webhook_url(public_base_url: str, webhook_path: str) -> str:
    if not webhook_path.startswith("/"):
        raise ValueError("Telegram webhook path must start with '/'")
    return f"{public_base_url.rstrip('/')}{webhook_path}"


async def inspect_telegram_webhook(
    bot: Bot,
    *,
    expected_url: str,
) -> TelegramWebhookStatus:
    info = await bot.get_webhook_info()
    return TelegramWebhookStatus(
        expected_url=expected_url,
        actual_url=info.url,
        pending_update_count=info.pending_update_count,
        last_error_message=info.last_error_message,
    )


async def verify_telegram_webhook(
    bot: Bot,
    *,
    expected_url: str,
) -> TelegramWebhookStatus:
    status = await inspect_telegram_webhook(bot, expected_url=expected_url)
    if status.actual_url != status.expected_url:
        raise TelegramWebhookError(
            "Telegram webhook URL does not match PUBLIC_BASE_URL and TELEGRAM_WEBHOOK_PATH"
        )
    return status


async def configure_telegram_webhook(
    bot: Bot,
    *,
    expected_url: str,
    secret_token: str,
    allowed_updates: list[str],
) -> TelegramWebhookStatus:
    configured = await bot.set_webhook(
        expected_url,
        secret_token=secret_token,
        allowed_updates=allowed_updates,
        drop_pending_updates=False,
    )
    if not configured:
        raise TelegramWebhookError("Telegram rejected the webhook configuration")
    return await verify_telegram_webhook(bot, expected_url=expected_url)


async def delete_telegram_webhook(bot: Bot) -> None:
    deleted = await bot.delete_webhook(drop_pending_updates=False)
    if not deleted:
        raise TelegramWebhookError("Telegram rejected the webhook deletion")
