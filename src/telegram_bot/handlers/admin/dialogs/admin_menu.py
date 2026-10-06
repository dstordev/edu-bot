from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Start
from aiogram_dialog.widgets.text import Const

from telegram_bot.handlers.admin.states import AddHomeworkSG, AddScheduleSG, AdminMenuSG
from telegram_bot.handlers.registered.general import command_start_handler_registered
from telegram_bot.utils.html_format import b


async def on_back_to_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    state = manager.middleware_data["state"]
    await command_start_handler_registered(callback, state, manager)


admin_menu_dialog = Dialog(
    Window(
        Const(b("🏜️ Меню админа")),
        Start(
            Const("➕ Добавить расписание замен"),
            state=AddScheduleSG.date,
            id="add_replacement_schedule",
        ),
        Start(
            Const("➕ Добавить домашнее задание"),
            state=AddHomeworkSG.academic_subject,
            id="add_homework",
        ),
        Button(Const("◀️ Назад"), on_click=on_back_to_menu, id="back_to_menu"),
        state=AdminMenuSG.main,
    ),
)
