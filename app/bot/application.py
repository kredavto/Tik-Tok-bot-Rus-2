from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.handlers import router
from app.bot.middleware import ActiveUserMiddleware
from app.core.config import settings


def create_dispatcher() -> Dispatcher:
    storage = RedisStorage.from_url(settings.redis_url)
    dispatcher = Dispatcher(storage=storage)
    dispatcher.update.outer_middleware(ActiveUserMiddleware())
    dispatcher.include_router(router)
    return dispatcher
