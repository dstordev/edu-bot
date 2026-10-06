from datetime import datetime

from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import ManagedTextInput, MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from loguru import logger

from db.repositories import DBRepositories
from telegram_bot.handlers.admin.getters import get_academic_subjects, get_groups
from telegram_bot.handlers.admin.handlers import (
    on_academic_subject_selected,
    on_date,
    on_group_selected,
)
from telegram_bot.handlers.admin.states import AddHomeworkSG
from telegram_bot.handlers.admin.widgets import (
    back_button,
    cancel_button,
    confirmation_row,
)
from telegram_bot.utils.html_format import b
from utils.datetime_format import DATE_FORMAT


# Обработчики
async def on_next(callback: CallbackQuery, button: Button, manager: DialogManager):
    """Обработчик пропуска этапа диалога."""
    await manager.next()


async def on_text(
    message: Message, widget: ManagedTextInput[str], manager: DialogManager, data: str
):
    """Обработчик ввода текста домашнего задания."""

    manager.dialog_data["text"] = data
    await manager.next()


async def on_files(message: Message, widget: MessageInput, manager: DialogManager):
    """Обработчик ввода фотографий или файлов."""

    if manager.dialog_data.get("files") is None:
        manager.dialog_data["files"] = []

    files = manager.dialog_data["files"]
    if message.photo:
        file_id = message.photo[-1].file_id
        files.append({"type": "photo", "file_id": file_id})
    elif message.document:
        file_id = message.document.file_id
        files.append({"type": "document", "file_id": file_id})


async def on_confirm(callback: CallbackQuery, button: Button, manager: DialogManager):
    """Обработчик подтверждения создания домашнего задания."""

    dbrepositories: DBRepositories = manager.middleware_data["dbrepositories"]

    # Создаем домашнее задание и материалы к нему
    academic_subject_id: int = int(manager.dialog_data["academic_subject"])
    text: str = manager.dialog_data["text"]
    files: list[dict] | None = manager.dialog_data.get("files")
    photo_file_ids: list[str] | None = None
    document_file_ids: list[str] | None = None
    if files:
        photo_file_ids = [
            file_data["file_id"] for file_data in files if file_data["type"] == "photo"
        ]
        document_file_ids = [
            file_data["file_id"]
            for file_data in files
            if file_data["type"] == "document"
        ]
    assignment_date: str | None = manager.dialog_data.get("date")
    group_id: int = int(manager.dialog_data["group"])

    try:
        await dbrepositories.homework.add_homework(
            group_id=group_id,
            academic_subject_id=academic_subject_id,
            text=text,
            assignment_date=datetime.strptime(assignment_date, DATE_FORMAT).date()  # noqa: DTZ007
            if assignment_date
            else None,
            photo_telegram_file_ids=photo_file_ids,
            file_telegram_file_ids=document_file_ids,
        )
    except Exception as ex:
        logger.exception(f"Не удалось создать домашнее задание: {ex}")
        await callback.answer(
            "😿 Произошла ошибка при создании домашнего задания, попробуйте позже",
            show_alert=True,
        )
        return

    await callback.answer("😺 Домашнее задание успешно записано", show_alert=True)
    await manager.done()


next_button = Button(Const("➡️ Дальше"), id="skip", on_click=on_next)

add_homework_dialog = Dialog(
    Window(
        Const(b("📚 Выберите учебный предмет:")),
        ScrollingGroup(
            Select(
                text=Format("{item[name]}"),
                id="academic_subject_select",
                item_id_getter=lambda x: x["id"],
                items="academic_subjects",
                on_click=on_academic_subject_selected,
            ),
            id="academic_subject_scroll",
            width=1,
            height=10,
        ),
        cancel_button,
        state=AddHomeworkSG.academic_subject,
        getter=get_academic_subjects,
    ),
    Window(
        Const(b("✏️ Введите текст домашнего задания:")),
        TextInput(id="text_input", on_success=on_text),
        back_button,
        state=AddHomeworkSG.text,
    ),
    Window(
        Const(
            b(
                "✏️ Отправьте фотографию или документ, чтобы прикрепить их к домашнему заданию"
            )
        ),
        MessageInput(on_files, content_types=[ContentType.PHOTO, ContentType.DOCUMENT]),
        next_button,
        back_button,
        state=AddHomeworkSG.photo_or_document,
    ),
    Window(
        Const(b("✏️ Введите дату, когда задали задание:")),
        TextInput(id="assignment_date_input", on_success=on_date),
        next_button,
        back_button,
        state=AddHomeworkSG.assignment_date,
    ),
    Window(
        Const(b("✏️ Выберите группу:")),
        ScrollingGroup(
            Select(
                text=Format("{item[name]}"),
                id="group_select",
                item_id_getter=lambda x: x["id"],
                items="groups",
                on_click=on_group_selected,
            ),
            id="group_scroll",
            width=1,
            height=10,
        ),
        back_button,
        state=AddHomeworkSG.group,
        getter=get_groups,
    ),
    Window(
        Format(
            b(
                "✏️ Вот так выглядит домашнее задание. Создаем?\n\n"
                "- Предмет: {dialog_data[academic_subject]}\n"
                "- Текст: {dialog_data[text]}"
            )
        ),
        confirmation_row(on_confirm),
        back_button,
        state=AddHomeworkSG.confirm,
    ),
)
