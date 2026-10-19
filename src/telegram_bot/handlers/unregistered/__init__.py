from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from db.repositories import DBRepositories
from telegram_bot.handlers.unregistered.dialog import dialog_router
from telegram_bot.handlers.unregistered.states import UnregisteredSG
from telegram_bot.utils.html_format import b

unregistered_router = Router(name=__name__)


@unregistered_router.message(CommandStart())
async def start_dialog(
    message: Message, dialog_manager: DialogManager, dbrepositories: DBRepositories
):
    if not await dbrepositories.group.get_groups():
        await message.answer(b("🐱 Группы еще не указаны, вернитесь немного позже"))
        return

    await dialog_manager.start(UnregisteredSG.group_token, mode=StartMode.RESET_STACK)


unregistered_router.include_router(dialog_router)

__all__ = ["unregistered_router"]
