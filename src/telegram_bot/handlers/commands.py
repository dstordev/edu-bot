# telegram_bot/handlers/commands.py
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from db.repositories import DBRepositories
from telegram_bot.handlers.registered.main_menu import MainMenuSG
from telegram_bot.handlers.unregistered.states import UnregisteredSG
from telegram_bot.utils.html_format import b

commands_router = Router(name=__name__)


@commands_router.message(CommandStart())
async def command_start(
    message: Message,
    dialog_manager: DialogManager,
    dbrepositories: DBRepositories,
) -> None:
    if not message.from_user:
        return

    # Проверяем, есть ли студент в базе
    student = await dbrepositories.student.find_by_telegram_id(message.from_user.id)

    if not student:
        # Если не зарегистрирован — проверяем группы и шлем на регистрацию
        groups = await dbrepositories.group.get_groups()
        if not groups:
            await message.answer(b("🐱 Группы еще не указаны, вернитесь немного позже"))
            return
        await dialog_manager.start(UnregisteredSG.group_token, mode=StartMode.RESET_STACK)
    else:
        # Если зарегистрирован — сразу открываем Главное Меню
        await dialog_manager.start(MainMenuSG.main, mode=StartMode.RESET_STACK)
