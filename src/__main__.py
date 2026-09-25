import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from loguru import logger
from redis.asyncio.client import Redis

from checks import check_postgres_connection, check_redis_connection
from db.connect import async_sessmaker
from schedule_notifier import ScheduleNotifier
from settings import settings
from telegram_bot.handlers import global_router
from telegram_bot.middlewares.db_session_middleware import DbSessionMiddleware
from telegram_bot.middlewares.log_middleware import LoggerMiddleware
from telegram_bot.middlewares.throttling_middleware import ThrottlingMiddleware

VERSION = "0.5.0"

logger.remove()
logger.add(sys.stderr, level="DEBUG")

logger.info(f"Версия приложения: {VERSION}")


async def main() -> None:
    # Проверки перед запуском
    logger.debug("Проверяю подключение к postgres...")
    if not await check_postgres_connection(async_sessmaker):
        return logger.warning("Не удалось подключится к postgres.")

    logger.debug("Проверяю подключение к REDIS...")
    if not await check_redis_connection(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT
    ):
        return logger.warning("Не удалось подключится к redis.")

    redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

    logger.debug("Настраиваю бота...")
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=RedisStorage(redis_client))
    dp.update.outer_middleware(DbSessionMiddleware(session_pool=async_sessmaker))

    global_router.message.middleware.register(ThrottlingMiddleware())
    global_router.callback_query.middleware.register(ThrottlingMiddleware())

    global_router.message.middleware.register(LoggerMiddleware())
    global_router.callback_query.middleware.register(LoggerMiddleware())
    dp.include_router(global_router)

    logger.debug("Запускаю ScheduleNotifier...")
    ScheduleNotifier(bot, async_sessmaker).run_monitor()

    logger.debug("Устанавливаю в бота команду /start...")
    await bot.set_my_commands(
        commands=[BotCommand(command="/start", description="🐱 Обновить бота")]
    )

    logger.debug("Запускаю бота...")
    dp.startup.register(lambda: logger.info("Бот запущен"))
    dp.workflow_data.update(
        async_sessmaker=async_sessmaker,
        ADMIN_IDS=settings.ADMIN_IDS,
        DEVELOPER_ID=settings.DEVELOPER_ID,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
