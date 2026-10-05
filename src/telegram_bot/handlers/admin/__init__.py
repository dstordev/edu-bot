from aiogram import Router

from telegram_bot.filters import IsAdminFilter

from .add_homework import add_homework_router
from .add_replacement_schedule import add_replacement_schedule_router
from .general import admin_general_router
from .homework import admin_homework_router

admin_router = Router()
admin_router.callback_query.filter(IsAdminFilter())
admin_router.message.filter(IsAdminFilter())

admin_router.include_routers(
    admin_general_router,
    add_homework_router,
    admin_homework_router,
    add_replacement_schedule_router,
)

__all__ = ["admin_router"]
