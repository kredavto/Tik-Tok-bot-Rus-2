import asyncio

from aiogram import Bot

from app.bot.application import create_dispatcher
from app.core.config import require_settings, settings, validate_runtime_settings
from app.core.logging import configure_logging
from app.db.session import init_db


async def main() -> None:
    configure_logging()
    require_settings("bot_token", "database_url", "redis_url")
    validate_runtime_settings()
    await init_db()

    bot = Bot(token=settings.bot_token)
    dispatcher = create_dispatcher()
    if settings.telegram_delivery_mode == "webhook":
        webhook_url = f"{settings.public_base_url.rstrip('/')}{settings.telegram_webhook_path}"
        await bot.set_webhook(
            webhook_url,
            secret_token=settings.telegram_webhook_secret,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
        await asyncio.Event().wait()
        return

    await bot.delete_webhook(drop_pending_updates=False)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
