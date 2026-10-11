from aiogram import Router

from telegram_bot.filters import IsRegisteredUserFilter

from .general import registered_general_router
from .homework import registered_homework_router
from .schedule import registered_schedule_router
from .student_settings import student_settings_router

registered_router = Router()
registered_router.message.filter(IsRegisteredUserFilter())
registered_router.callback_query.filter(IsRegisteredUserFilter())

registered_router.include_routers(
    registered_homework_router,
    registered_general_router,
    registered_schedule_router,
    student_settings_router,
)


__all__ = ["registered_router"]
