from aiogram import Router

from telegram_bot.filters import IsAdminFilter

from .homework import admin_homework_router
from .presence import admin_presence_router

admin_router = Router()
admin_router.callback_query.filter(IsAdminFilter())
admin_router.message.filter(IsAdminFilter())

admin_router.include_routers(admin_homework_router, admin_presence_router)

__all__ = ["admin_router"]
