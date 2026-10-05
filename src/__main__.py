import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand
from aiogram_dialog import setup_dialogs
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from redis.asyncio import Redis

from auto_update_replacement_schedule.service import check_schedule_updates
from checks import check_postgres_connection, check_redis_connection
from db.connect import async_sessmaker
from schedule_notifier import ScheduleNotifier
from settings import settings
from telegram_bot.handlers import global_router
from telegram_bot.middlewares.db_session_middleware import DbSessionMiddleware
from telegram_bot.middlewares.log_middleware import LoggerMiddleware
from telegram_bot.middlewares.throttling_middleware import ThrottlingMiddleware
from utils.timezones import TZ_MOSCOW_RAW

VERSION = "0.6.0"

logger.remove()
logger.add(sys.stderr, level="DEBUG")

logger.info(f"Версия приложения: {VERSION}")


scheduler = AsyncIOScheduler(timezone=TZ_MOSCOW_RAW)


async def on_startup(bot: Bot, redis: Redis) -> None:
    # Запускаем проверку каждые 5 минут с 06:00 до 22:55
    scheduler.add_job(
        check_schedule_updates,
        trigger=CronTrigger(minute="*/5", hour="6-22", timezone=TZ_MOSCOW_RAW),
        id="schedule_checker_job",
        name="Проверка расписания замен в telemost",
        kwargs={
            "study_chat_id": settings.TELEMOST_CHAT_ID,
            "session_id": settings.SESSION_ID_YANDEX,
            "user_id": settings.USER_ID_YANDEX,
            "redis": redis,
            "bot": bot,
            "async_sessmaker": async_sessmaker,
        },
        max_instances=1,  # Защита: следующий запуск не начнется, пока идет предыдущий
        coalesce=True,  # Если бот завис, пропущенные запуски объединятся в один
    )
    scheduler.start()
    logger.debug("APScheduler запущен.")


async def on_shutdown() -> None:
    scheduler.shutdown(wait=False)
    logger.debug("APScheduler остановлен.")


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

    dp = Dispatcher(
        storage=RedisStorage(
            redis_client, key_builder=DefaultKeyBuilder(with_destiny=True)
        )
    )
    dp.update.outer_middleware(DbSessionMiddleware(session_pool=async_sessmaker))

    global_router.message.middleware.register(ThrottlingMiddleware())
    global_router.callback_query.middleware.register(ThrottlingMiddleware())

    global_router.message.middleware.register(LoggerMiddleware())
    global_router.callback_query.middleware.register(LoggerMiddleware())
    dp.include_router(global_router)

    setup_dialogs(dp)

    logger.debug("Запускаю ScheduleNotifier...")
    ScheduleNotifier(bot, async_sessmaker).run_monitor()

    logger.debug("Регистрирую запуск автообновления расписания...")
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.debug("Устанавливаю команды в бота...")
    await bot.set_my_commands(
        commands=[BotCommand(command="/start", description="🐱 Обновить бота")]
    )

    logger.debug("Запускаю бота...")
    dp.startup.register(lambda: logger.info("Бот запущен"))
    dp.workflow_data.update(
        async_sessmaker=async_sessmaker,
        ADMIN_IDS=settings.ADMIN_IDS,
        redis=redis_client,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
