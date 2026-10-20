from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.text.multi import Case

from telegram_bot.handlers.unregistered.getters import (
    getter_group_token,
    getter_student_name,
)
from telegram_bot.handlers.unregistered.handlers import on_group_token, on_student_name
from telegram_bot.handlers.unregistered.states import UnregisteredSG
from telegram_bot.utils.html_format import b

dialog_router = Dialog(
    Window(
        Case(
            texts={
                False: Const(b("✏️ Введите код доступа к своей группе ниже:")),
                True: Const(
                    b(
                        "🐈️ Этот код мне не знаком, перепроверьте правильность набора и попробуйте еще раз:"
                    )
                ),
            },
            selector="has_error",
        ),
        TextInput(id="text_input", on_success=on_group_token),
        state=UnregisteredSG.group_token,
        getter=getter_group_token,
    ),
    Window(
        Case(
            texts={
                False: Const(b("✏️ Введите свои ФИО или ФИ:")),
                True: Const(
                    b(
                        "⚠️ Введите ФИО или ФИ (например: Иванов Иван Иванович или Иванов Иван). Попробуйте ещё раз:"
                    )
                ),
            },
            selector="has_error",
        ),
        TextInput(id="text_input", on_success=on_student_name),
        state=UnregisteredSG.student_name,
        getter=getter_student_name,
    ),
)
