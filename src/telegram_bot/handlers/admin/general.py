from aiogram import F, Router
from aiogram.types import CallbackQuery

from telegram_bot.buttons.other import admin_menu_b
from telegram_bot.windows.registered import admin_menu_window

admin_general_router = Router()


@admin_general_router.callback_query(F.data == admin_menu_b.callback_data)
async def admin_menu(callback: CallbackQuery):
    await admin_menu_window().answer_window(callback)
