from aiogram import Bot
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import ManagedTextInput
from loguru import logger

from db.repositories import DBRepositories
from telegram_bot.handlers.registered.main_menu import MainMenuSG
from telegram_bot.utils.html_format import b
from utils.notify.admins import notify_admins


async def on_group_token(
    message: Message,
    widget: ManagedTextInput[str],
    manager: DialogManager,
    data: str,
):
    repos: DBRepositories = manager.middleware_data["dbrepositories"]
    if not (group := await repos.group.find_by_token(data)):
        manager.dialog_data["token_not_found"] = True
        return

    manager.dialog_data["group_id"] = group.id
    await manager.next()


async def on_student_name(
    message: Message,
    widget: ManagedTextInput[str],
    manager: DialogManager,
    data: str,
):
    if not message.from_user:
        logger.warning("Полученное сообщение ожидается от пользователя.")
        return

    repos: DBRepositories = manager.middleware_data["dbrepositories"]
    bot: Bot = manager.middleware_data["bot"]
    group_id: int = manager.dialog_data["group_id"]
    student_name = data

    # Проверка правильности введенного имени
    parts = [p.strip(" ,;.\t\n\r") for p in student_name.strip().split() if p.strip()]
    if len(parts) < 2:
        manager.dialog_data["bad_student_name"] = True
        return

    if len(parts) == 2:
        surname, name = parts[0], parts[1]
        patronymic = ""
    else:
        surname = parts[0]
        name = parts[1]
        patronymic = " ".join(parts[2:])

    # Создание студента в бд
    student_id = await repos.student.create(
        telegram_id=message.from_user.id,
        surname=surname,
        name=name,
        patronymic=patronymic,
        group_id=group_id,
    )
    await repos.student_settings.add(student_id)

    # Уведомление пользователя
    await message.answer(b("😸 Успешно вас зарегистрировал!"))

    # Уведомление админов
    await notify_admins(b("😸 Зарегистрирован новый пользователь!"), bot)

    # Редирект в главное меню
    await manager.start(MainMenuSG.main, mode=StartMode.RESET_STACK)
