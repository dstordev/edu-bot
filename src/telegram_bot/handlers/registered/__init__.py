from aiogram import Router

from telegram_bot.filters import IsRegisteredUserFilter

from .homework import registered_homework_router
from .main_menu import main_menu_dialog
from .schedule import registered_schedule_router
from .student_settings import student_settings_router

registered_router = Router()
registered_router.message.filter(IsRegisteredUserFilter())
registered_router.callback_query.filter(IsRegisteredUserFilter())

registered_router.include_routers(
    main_menu_dialog,
    registered_schedule_router,
    registered_homework_router,
    student_settings_router,
)

__all__ = ["registered_router"]
