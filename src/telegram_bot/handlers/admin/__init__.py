from aiogram import Router

from telegram_bot.filters import IsAdminFilter
from telegram_bot.handlers.admin.dialogs.add_homework import add_homework_dialog
from telegram_bot.handlers.admin.dialogs.add_replacement_schedule import add_schedule_dialog
from telegram_bot.handlers.admin.dialogs.admin_menu import admin_menu_dialog

admin_router = Router()
admin_router.callback_query.filter(IsAdminFilter())
admin_router.message.filter(IsAdminFilter())


admin_router.include_routers(
    admin_menu_dialog,
    add_homework_dialog,
    add_schedule_dialog,
)

__all__ = ["admin_router"]
