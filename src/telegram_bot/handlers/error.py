from aiogram import Bot, Router, html
from aiogram.exceptions import AiogramError
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.api.exceptions import OutdatedIntent, UnknownIntent, UnknownState
from loguru import logger

from telegram_bot.utils.html_format import b, blockquote, code
from utils.notify.admins import notify_admins

error_router = Router(name=__name__)


@error_router.errors(ExceptionTypeFilter(UnknownIntent, OutdatedIntent))
async def on_intent_error(err_event: ErrorEvent) -> bool:
    # Если ошибку вызвал клик по старой кнопке
    if event := err_event.update.callback_query:
        await event.answer("😺 Это сообщение устарело. Откройте меню заново", show_alert=True)

        # Удаляем "мёртвое" сообщение, чтобы по нему больше не кликали
        try:
            if (message := event.message) and isinstance(message, Message):
                await message.delete()
        except AiogramError:
            pass

    return True


@error_router.error()
async def error_handler(err_event: ErrorEvent, bot: Bot) -> None:
    safe_text = html.quote(str(err_event.exception))
    dev_error_text = f"⭕ Произошла неизвестная ошибка: {blockquote(safe_text)}"

    # Выясняем вызвал ли ошибку пользователь
    from_user = None
    if (event := err_event.update.callback_query) or (event := err_event.update.message):
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
    await notify_admins(dev_error_text, bot)


async def on_unknown_state(event: ErrorEvent, dialog_manager: DialogManager) -> None:
    # При обнаружении мертвого/неизвестного стейта — просто сбрасываем стек
    await dialog_manager.reset_stack()


error_router.errors.register(on_unknown_state, ExceptionTypeFilter(UnknownState))
error_router.errors.register(on_unknown_state, ExceptionTypeFilter(UnknownIntent))
