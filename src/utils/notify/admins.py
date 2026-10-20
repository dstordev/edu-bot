from aiogram import Bot
from aiogram.exceptions import AiogramError

from settings import settings


async def notify_admins(text: str, bot: Bot) -> tuple[int, int]:
    """
    Возвращает кол-во админов и кол-во неудачных попыток.
    """

    count = len(settings.ADMIN_IDS)
    err_count = 0
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except AiogramError:
            err_count += 1
    return count, err_count
