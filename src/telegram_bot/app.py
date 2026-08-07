from typing import Any

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from redis.asyncio.client import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from telegram_bot.handlers import global_router
from telegram_bot.middlewares.db_session_middleware import DbSessionMiddleware
from telegram_bot.middlewares.log_middleware import LoggerMiddleware
from telegram_bot.middlewares.throttling_middleware import ThrottlingMiddleware


class TelegramBotApp:
    def __init__(
        self,
        bot_token: str,
        redis: Redis,
        async_session_maker: async_sessionmaker[AsyncSession],
    ):
        self.__bot = Bot(
            token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        self.redis: Redis = redis
        self.async_session_maker = async_session_maker
        self.dp = Dispatcher(storage=RedisStorage(self.redis))

        self.__set_middlewares(global_router)
        self.dp.include_router(global_router)

    @property
    def bot(self) -> Bot:
        return self.__bot

    async def set_start_command(self) -> None:
        await self.__bot.set_my_commands(
            commands=[BotCommand(command="/start", description="🐱 Обновить бота")]
        )

    async def start_polling_telegram_bot(self, startup: Any = None, **kwargs) -> None:
        self.dp.startup.register(startup)
        self.dp.workflow_data.update(**kwargs)
        await self.dp.start_polling(self.__bot)

    def __set_middlewares(self, router: Router):
        self.dp.update.outer_middleware(
            DbSessionMiddleware(session_pool=self.async_session_maker)
        )

        router.message.middleware.register(ThrottlingMiddleware())
        router.callback_query.middleware.register(ThrottlingMiddleware())

        router.message.middleware.register(LoggerMiddleware())
        router.callback_query.middleware.register(LoggerMiddleware())
