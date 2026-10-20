from aiogram import Router

from telegram_bot.handlers.unregistered.dialog import dialog_router

unregistered_router = Router(name=__name__)
unregistered_router.include_router(dialog_router)

__all__ = ["unregistered_router"]
