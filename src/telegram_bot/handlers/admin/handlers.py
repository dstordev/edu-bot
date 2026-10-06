from datetime import datetime

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Select
from loguru import logger

from utils.datetime_format import DATE_FORMAT


async def on_academic_subject_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    """Обработчик выбора учебного предмета."""

    manager.dialog_data["academic_subject"] = item_id
    await manager.next()


async def on_group_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    """Обработчик выбора группы."""

    manager.dialog_data["group"] = item_id
    await manager.next()


async def on_date(
    message: Message, widget: ManagedTextInput[str], manager: DialogManager, data: str
):
    """Обработчик ввода даты."""

    try:
        datetime.strptime(data, DATE_FORMAT).date()  # noqa: DTZ007
    except Exception as ex:
        return logger.warning(f"Не удалось спарсить введенную дату: {ex}")

    manager.dialog_data["date"] = data
    await manager.next()
