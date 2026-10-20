from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from db.repositories import DBRepositories
from telegram_bot.filters import IsRegisteredUserFilter
from telegram_bot.handlers.registered.main_menu import MainMenuSG

commands_router = Router(name=__name__)


@commands_router.message(IsRegisteredUserFilter(), CommandStart())
async def command_start(
    message: Message, dialog_manager: DialogManager, dbrepositories: DBRepositories
) -> None:
    await dialog_manager.start(MainMenuSG.main, mode=StartMode.RESET_STACK)
