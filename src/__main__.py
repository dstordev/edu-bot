import asyncio
import sys

from loguru import logger
from redis.asyncio.client import Redis

from db.connect import async_sessmaker
from schedule_notifier import ScheduleNotifier
from settings import settings
from telegram_bot.app import TelegramBotApp

VERSION = "0.5.0"

logger.remove()
logger.add(sys.stderr, level="DEBUG")

logger.info(f"Версия приложения: {VERSION}")


async def main() -> None:
    logger.debug("Настраиваю подключение к REDIS...")
    redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

    telegram_bot_app = TelegramBotApp(
        settings.BOT_TOKEN, redis=redis, async_session_maker=async_sessmaker
    )

    logger.debug("Запускаю ScheduleNotifier...")
    ScheduleNotifier(telegram_bot_app.bot, async_sessmaker).run_monitor()

    logger.debug("Устанавливаю в бота команду /start...")
    await telegram_bot_app.set_start_command()

    logger.debug("Запускаю бота...")
    await telegram_bot_app.start_polling_telegram_bot(
        async_sessmaker=async_sessmaker,
        ADMIN_IDS=settings.ADMIN_IDS,
        DEVELOPER_ID=settings.DEVELOPER_ID,
        startup=lambda: logger.info("Бот запущен"),
    )


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    asyncio.run(main())
