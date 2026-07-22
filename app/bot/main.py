import asyncio
import logging

from aiogram import Bot

from app.bot.application import create_dispatcher
from app.core.config import require_settings, settings, validate_runtime_settings
from app.core.logging import configure_logging
from app.db.session import init_db
from app.services.telegram_webhook import (
    TelegramWebhookError,
    build_telegram_webhook_url,
    verify_telegram_webhook,
)

logger = logging.getLogger(__name__)


async def monitor_webhook(bot: Bot) -> None:
    expected_url = build_telegram_webhook_url(
        settings.public_base_url,
        settings.telegram_webhook_path,
    )
    while True:
        try:
            status = await verify_telegram_webhook(bot, expected_url=expected_url)
            logger.info(
                "Telegram webhook monitor passed",
                extra={"pending_update_count": status.pending_update_count},
            )
        except TelegramWebhookError as exc:
            logger.warning("Telegram webhook monitor detected configuration drift: %s", exc)
        except Exception:
            # Provider exceptions may contain request URLs; keep the bot token out of logs.
            logger.warning("Telegram webhook monitor could not contact Telegram")
        await asyncio.sleep(settings.telegram_webhook_check_seconds)


async def main() -> None:
    configure_logging()
    require_settings("bot_token", "database_url", "redis_url")
    validate_runtime_settings()
    bot = Bot(token=settings.bot_token)
    if settings.telegram_delivery_mode == "webhook":
        try:
            await monitor_webhook(bot)
        finally:
            await bot.session.close()
        return

    await init_db()
    dispatcher = create_dispatcher()
    await bot.delete_webhook(drop_pending_updates=False)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
