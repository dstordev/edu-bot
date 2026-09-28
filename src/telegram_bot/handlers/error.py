from aiogram import Bot, Router, html
from aiogram.types import ErrorEvent
from loguru import logger

from settings import settings
from telegram_bot.utils.html_format import b, blockquote, code

error_router = Router(name=__name__)


@error_router.error()
async def error_handler(err_event: ErrorEvent, bot: Bot):
    safe_text = html.quote(str(err_event.exception))
    dev_error_text = f"⭕ Произошла неизвестная ошибка: {blockquote(safe_text)}"

    # Выясняем вызвал ли ошибку пользователь
    from_user = None
    if err_event.update.callback_query:
        from_user = err_event.update.callback_query.from_user
    elif err_event.update.message:
        from_user = err_event.update.message.from_user

    # При возможности уведомляем пользователя, который вызывал ошибку
    if from_user:
        error_text = "😿 Упс, что-то пошло не так. Пожалуйста, попробуйте позже"
        if err_event.update.message is not None:
            await err_event.update.message.answer(b(error_text))
        elif err_event.update.callback_query is not None:
            await err_event.update.callback_query.answer(error_text, show_alert=True)

        dev_error_text += f"\n- Её вызвал пользователь: {code(from_user.id)}"
        if from_user.username:
            dev_error_text += f" | @{from_user.username}"

    # Уведомляем разработчика об ошибке
    logger.exception(dev_error_text)
    await bot.send_message(settings.DEVELOPER_ID, dev_error_text)
