from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from loguru import logger


class LoggerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if event.from_user:
                logger.info(
                    f"Бот обрабатывает сообщение: {event.text} | Пользователь: {event.from_user.id}"
                )
            else:
                logger.info(
                    f"Бот обрабатывает сообщение: {event.text} | Пользователь: {event.from_user}"
                )
        elif isinstance(event, CallbackQuery):
            logger.info(
                f"Бот обрабатывает кнопку: {event.data} | Пользователь: {event.from_user.id}"
            )

        result = await handler(event, data)

        return result
