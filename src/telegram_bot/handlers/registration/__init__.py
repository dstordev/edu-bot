from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from db.repositories import DBRepositories
from telegram_bot.utils.html_format import b

from .dialog import dialog_router
from .states import RegistrationSG

registration_router = Router(name=__name__)


@registration_router.message(CommandStart())
async def command_start(
    message: Message, dialog_manager: DialogManager, dbrepositories: DBRepositories
) -> None:
    groups = await dbrepositories.group.get_groups()
    if not groups:
        await message.answer(b("🐱 Группы еще не указаны, вернитесь немного позже"))
        return
    await dialog_manager.start(RegistrationSG.group_token, mode=StartMode.RESET_STACK)


registration_router.include_router(dialog_router)

__all__ = ["registration_router"]
