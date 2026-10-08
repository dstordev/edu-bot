from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from loguru import logger

from db.repositories import DBRepositories


class ActivityStudentsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, (Message, CallbackQuery)):
            from_user = event.from_user
            repos: DBRepositories | None = data.get("dbrepositories")
            if from_user and repos:
                found_student = await repos.student.find_by_telegram_id(from_user.id)
                if found_student:
                    if not found_student.is_active:
                        try:
                            await repos.student.mark_activity(
                                found_student.id, is_active=True
                            )
                        except Exception as ex:
                            logger.error(
                                f"Не удалось пометить активность студента: {ex}"
                            )
                else:
                    logger.warning(
                        f"Не удалось найти пользователя {from_user.username or from_user.id} в студентах."
                    )
            else:
                if not from_user:
                    logger.warning(
                        "[ActivityStudentsMiddleware] Не удалось найти пользователя из события."
                    )
                else:
                    logger.warning(
                        "[ActivityStudentsMiddleware] Не удалось найти dbrepositories из data. Возможно мидлварь стоит выше чем нужно."
                    )
        else:
            logger.warning(
                f"[ActivityStudentsMiddleware] Неизвестный тип события - пропускаем обработку. Событие: {event}"
            )

        return await handler(event, data)
