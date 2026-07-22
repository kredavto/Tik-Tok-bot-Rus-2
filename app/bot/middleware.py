from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.db.session import get_or_create_user, session_scope


class ActiveUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_user = data.get("event_from_user")
        if telegram_user is None:
            return await handler(event, data)

        async with session_scope() as session:
            user = await get_or_create_user(
                session,
                telegram_user.id,
                telegram_user.username,
            )
            is_blocked = user.is_blocked

        if not is_blocked:
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer("Доступ к боту временно ограничен.", show_alert=True)
        elif isinstance(event, Message):
            await event.answer("Доступ к боту временно ограничен.")
        return None
