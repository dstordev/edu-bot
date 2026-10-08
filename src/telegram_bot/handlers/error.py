from aiogram import Bot, Router, html
from aiogram.exceptions import AiogramError
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent, Message
from aiogram_dialog.api.exceptions import OutdatedIntent, UnknownIntent
from loguru import logger

from settings import settings
from telegram_bot.utils.html_format import b, blockquote, code

error_router = Router(name=__name__)


@error_router.errors(ExceptionTypeFilter(UnknownIntent, OutdatedIntent))
async def on_intent_error(err_event: ErrorEvent):
    # Если ошибку вызвал клик по старой кнопке
    if event := err_event.update.callback_query:
        await event.answer(
            "😺 Это сообщение устарело. Откройте меню заново", show_alert=True
        )

        # Удаляем "мёртвое" сообщение, чтобы по нему больше не кликали
        try:
            if (message := event.message) and isinstance(message, Message):
                await message.delete()
        except AiogramError:
            pass

    return True


@error_router.error()
async def error_handler(err_event: ErrorEvent, bot: Bot):
    safe_text = html.quote(str(err_event.exception))
    dev_error_text = f"⭕ Произошла неизвестная ошибка: {blockquote(safe_text)}"

    # Выясняем вызвал ли ошибку пользователь
    from_user = None
    if (event := err_event.update.callback_query) or (
        event := err_event.update.message
    ):
        from_user = event.from_user

    # При возможности уведомляем пользователя, который вызывал ошибку
    if from_user:
        error_text = "😿 Упс, что-то пошло не так. Пожалуйста, попробуйте позже"
        try:
            if (event := err_event.update.message) is not None:
                await event.answer(b(error_text))
            elif (event := err_event.update.callback_query) is not None:
                await event.answer(error_text, show_alert=True)
        except AiogramError as ex:
            logger.error(f"Не удалось отправить сообщение об ошибке пользователю: {ex}")

        dev_error_text += f"\n- Её вызвал пользователь: {code(from_user.id)}"
        if from_user.username:
            dev_error_text += f" | @{from_user.username}"

    # Уведомляем админов об ошибке
    logger.exception(dev_error_text)
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, dev_error_text)
        except AiogramError as ex:
            logger.error(
                f"Не удалось отправить сообщение о произошедей ошибке админу {admin_id}: {ex}"
            )
