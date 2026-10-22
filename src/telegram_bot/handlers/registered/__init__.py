from aiogram import Router

from telegram_bot.filters import IsRegisteredUserFilter

from .homework import homework_dialog
from .main_menu import main_menu_dialog
from .schedule import schedule_dialog
from .student_settings import student_settings_dialog

registered_router = Router()
registered_router.message.filter(IsRegisteredUserFilter())
registered_router.callback_query.filter(IsRegisteredUserFilter())

registered_router.include_routers(
    main_menu_dialog,
    schedule_dialog,
    homework_dialog,
    student_settings_dialog,
)

__all__ = ["registered_router"]
