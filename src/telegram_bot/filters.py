from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject
from loguru import logger

from db.repositories import DBRepositories


class IsAdminFilter(BaseFilter):
    async def __call__(
        self, event: Message | CallbackQuery, ADMIN_IDS: list[int]
    ) -> bool:
        if not event.from_user:
            logger.warning("У события отсутствует пользователь.")
            return False

        return event.from_user.id in ADMIN_IDS


class IsRegisteredUserFilter(BaseFilter):
    async def __call__(
        self,
        event: TelegramObject,
        dbrepositories: DBRepositories,
    ) -> bool:
        if not isinstance(event, Message) and not isinstance(event, CallbackQuery):  # pyright: ignore[reportUnnecessaryIsInstance]
            return False

        if event.from_user:
            user_id = event.from_user.id

            result = await dbrepositories.student.find_by_telegram_id(user_id)

            return result is not None

        return False
