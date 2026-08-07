import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware для защиты от флуда/спама.
    Ограничивает количество запросов от пользователя за определенный период времени.
    """

    def __init__(
        self,
        default_rate: float = 0.7,  # Минимальный интервал между сообщениями (секунды)
        default_key: str | None = None,  # Ключ для группировки (по умолчанию - user_id)
    ):
        """
        Args:
            default_rate: Минимальный интервал между запросами в секундах
            default_key: Ключ для идентификации пользователя (по умолчанию используется user_id)
        """
        super().__init__()
        self.default_rate = default_rate
        self.default_key = default_key
        # Хранилище: {user_id: {"last_time": timestamp, "count": count}}
        self.cache: dict[int, dict[str, float]] = defaultdict(dict)

    def _get_user_id(self, event: Message | CallbackQuery) -> int | None:
        """Получить user_id из события"""
        if isinstance(event, (Message, CallbackQuery)):
            return event.from_user.id if event.from_user else None
        return None

    def _check_throttle(self, user_id: int, rate: float) -> bool:
        """
        Проверить, можно ли обработать запрос от пользователя.

        Returns:
            True - если запрос можно обработать
            False - если пользователь флудит
        """
        current_time = time.time()
        user_data = self.cache.get(user_id, {})

        last_time = user_data.get("last_time", 0)
        time_passed = current_time - last_time

        # Если прошло достаточно времени
        if time_passed >= rate:
            self.cache[user_id] = {"last_time": current_time}
            return True

        return False

    async def __call__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        """
        Основная логика middleware
        """
        user_id = self._get_user_id(event)

        if user_id is None:
            # Если не удалось получить user_id, пропускаем проверку
            return await handler(event, data)

        # Получаем rate из data или используем default
        rate = data.get("throttling_rate", self.default_rate)

        # Проверяем throttling
        if not self._check_throttle(user_id, rate):
            # Флуд обнаружен
            if isinstance(event, CallbackQuery):
                # Для callback query отвечаем alert'ом
                await event.answer(
                    "🐈 Слишком частые запросы. Пожалуйста, подождите", show_alert=True
                )
            elif isinstance(event, Message):
                # Для сообщений можно отправить предупреждение
                await event.answer("🐈 Слишком частые запросы. Пожалуйста, подождите")

            # Не вызываем handler
            return None

        # Пользователь прошел проверку, вызываем handler
        return await handler(event, data)
