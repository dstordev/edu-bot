from aiogram import F, Router
from aiogram.types import CallbackQuery

from telegram_bot.buttons.homework import homework_menu_b
from telegram_bot.windows.homework import homework_menu_window

admin_homework_router = Router()


@admin_homework_router.callback_query(F.data == homework_menu_b.callback_data)
async def handler_homework_menu(event: CallbackQuery):
    """
    Обрабатывает нажатие кнопки '📙 Домашние задания'.
    Отправляет меню с кнопкой админа для добавления домашнего задания.
    """

    await homework_menu_window(add_btn=True).answer_window(event)
