from __future__ import annotations

import argparse
import asyncio
import logging

from aiogram import Bot

from app.bot.application import create_dispatcher
from app.core.config import require_settings, settings, validate_runtime_settings
from app.core.logging import configure_logging
from app.services.telegram_webhook import (
    TelegramWebhookError,
    build_telegram_webhook_url,
    configure_telegram_webhook,
    delete_telegram_webhook,
    verify_telegram_webhook,
)

logger = logging.getLogger(__name__)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the production Telegram webhook")
    parser.add_argument("action", choices=("configure", "verify", "delete"))
    return parser


async def run(action: str) -> int:
    require_settings("bot_token")
    if action != "delete":
        validate_runtime_settings()

    bot = Bot(token=settings.bot_token)
    expected_url = build_telegram_webhook_url(
        settings.public_base_url,
        settings.telegram_webhook_path,
    )
    try:
        if action == "configure":
            require_settings("telegram_webhook_secret")
            dispatcher = create_dispatcher()
            try:
                allowed_updates = dispatcher.resolve_used_update_types()
                status = await configure_telegram_webhook(
                    bot,
                    expected_url=expected_url,
                    secret_token=settings.telegram_webhook_secret,
                    allowed_updates=allowed_updates,
                )
            finally:
                await dispatcher.storage.close()
        elif action == "verify":
            status = await verify_telegram_webhook(bot, expected_url=expected_url)
        else:
            await delete_telegram_webhook(bot)
            logger.info("Telegram webhook deleted")
            return 0
    except TelegramWebhookError as exc:
        logger.error("Telegram webhook operation failed: %s", exc)
        return 1
    except Exception:
        # Provider exceptions may contain request URLs; keep the bot token out of logs.
        logger.error("Telegram webhook operation failed because Telegram is unavailable")
        return 1
    finally:
        await bot.session.close()

    logger.info(
        "Telegram webhook verified",
        extra={
            "webhook_url": status.actual_url,
            "pending_update_count": status.pending_update_count,
            "has_last_error": bool(status.last_error_message),
        },
    )
    return 0


def main() -> None:
    configure_logging()
    args = _parser().parse_args()
    raise SystemExit(asyncio.run(run(args.action)))


if __name__ == "__main__":
    main()
