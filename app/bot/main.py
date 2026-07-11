import asyncio

from aiogram import Bot, Dispatcher

from app.core.config import require_settings, settings
from app.core.logging import configure_logging
from app.db.session import init_db
from .handlers import router


async def main() -> None:
    configure_logging()
    require_settings("bot_token", "database_url", "redis_url")
    await init_db()

    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
