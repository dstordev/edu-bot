from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

from telegram_bot.buttons.other import student_settings_b
from telegram_bot.handlers.registered.general import command_start_handler_registered
from telegram_bot.utils.html_format import b, i

student_settings_router = Router(name=__name__)


@student_settings_router.callback_query(F.data == student_settings_b.callback_data)
async def student_settings_menu(callback: CallbackQuery, dialog_manager: DialogManager):
    await dialog_manager.start(StudentSettingsSG.main, mode=StartMode.RESET_STACK)


class StudentSettingsSG(StatesGroup):
    main = State()


async def on_back_to_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
):
    state = manager.middleware_data["state"]
    await command_start_handler_registered(callback, state, manager)


student_settings_dialog = Dialog(
    Window(
        Const(b("⚙️ Настройки\n") + i("Тут ты можешь настроить что-то под себя.")),
        Button(Const("◀️ Назад"), on_click=on_back_to_menu, id="back_to_menu"),
        state=StudentSettingsSG.main,
    ),
)

student_settings_router.include_router(student_settings_dialog)
