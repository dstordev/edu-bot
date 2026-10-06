from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode

from telegram_bot.buttons.other import admin_menu_b
from telegram_bot.filters import IsAdminFilter
from telegram_bot.handlers.admin.dialogs.add_homework import add_homework_dialog
from telegram_bot.handlers.admin.dialogs.add_replacement_schedule import (
    add_schedule_dialog,
)
from telegram_bot.handlers.admin.dialogs.admin_menu import admin_menu_dialog
from telegram_bot.handlers.admin.states import AdminMenuSG

admin_router = Router()
admin_router.callback_query.filter(IsAdminFilter())
admin_router.message.filter(IsAdminFilter())
# Чтобы пропускать команды, потому что aiogram_dialog перехватывает все события,
# включая команду /start когда тебе нужно быстро выйти с добавления домашнего задания.
admin_router.message.filter(~F.text.startswith("/"))


@admin_router.callback_query(F.data == admin_menu_b.callback_data)
async def admin_menu(callback: CallbackQuery, dialog_manager: DialogManager):
    await dialog_manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


admin_router.include_routers(
    admin_menu_dialog,
    add_homework_dialog,
    add_schedule_dialog,
)

__all__ = ["admin_router"]
