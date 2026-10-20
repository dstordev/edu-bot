from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Cancel, Start
from aiogram_dialog.widgets.text import Const

from telegram_bot.handlers.admin.states import AddHomeworkSG, AddScheduleSG, AdminMenuSG
from telegram_bot.utils.html_format import b

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
        Cancel(Const("◀️ Назад")),
        state=AdminMenuSG.main,
    ),
)
