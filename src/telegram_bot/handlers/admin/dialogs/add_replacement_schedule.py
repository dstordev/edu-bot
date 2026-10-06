from datetime import datetime

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Column, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format

from db.repositories import DBRepositories
from telegram_bot.handlers.admin.getters import get_academic_subjects, get_groups
from telegram_bot.handlers.admin.handlers import (
    on_academic_subject_selected,
    on_date,
    on_group_selected,
)
from telegram_bot.handlers.admin.states import AddScheduleSG
from telegram_bot.handlers.admin.widgets import back_button, cancel_button
from utils.datetime_format import DATE_FORMAT


# === Геттеры ===
async def get_classes(dbrepositories: DBRepositories, **kwargs):
    """Геттер для получения номеров пар."""

    classes = await dbrepositories.class_.get_classes()
    return {
        "classes": [
            {
                "id": str(class_.id),
                "number": class_.number,
                "start_at": class_.start_at,
                "end_at": class_.end_at,
            }
            for class_ in classes
        ]
    }


async def get_class_types(dbrepositories: DBRepositories, **kwargs):
    """Геттер для получения типов пар."""

    class_types = await dbrepositories.class_type.get_all()
    return {
        "class_types": [
            {"id": class_type.id, "name": class_type.name} for class_type in class_types
        ]
    }


async def get_audiences(dbrepositories: DBRepositories, **kwargs):
    """Геттер для получения аудиторий."""

    audiences = await dbrepositories.audience.get_all()
    return {
        "audiences": [
            {"id": audience.id, "name": audience.name} for audience in audiences
        ],
    }


# === Обработчики ===
async def on_class_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    """Обработчик выбора пары."""

    manager.dialog_data["class_"] = item_id
    await manager.next()


async def on_class_type_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    """Обработчик выбора типа пары."""

    manager.dialog_data["class_type"] = item_id
    await manager.next()


async def on_audience_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    """Обработчик выбора аудитории."""

    dbrepositories: DBRepositories = manager.middleware_data["dbrepositories"]

    # TODO: исправить предупреждение ruff о timezone
    date_ = datetime.strptime(manager.dialog_data["date"], DATE_FORMAT).date()  # noqa: DTZ007
    group_id = int(manager.dialog_data["group"])
    class_id = int(manager.dialog_data["class_"])
    academic_subject_id = int(manager.dialog_data["academic_subject"])
    class_type_id = int(manager.dialog_data["class_type"])
    audience_id = int(item_id)

    r = await dbrepositories.replacement_schedule.add(
        date_, group_id, class_id, academic_subject_id, class_type_id, audience_id
    )

    await callback.answer(f"Пара добавлена, id: {r.id}", show_alert=True)
    await manager.done()


add_schedule_dialog = Dialog(
    Window(
        Const("Введите дату (формат дд.мм.гггг):"),
        TextInput(
            id="date_input",
            on_success=on_date,
        ),
        cancel_button,
        state=AddScheduleSG.date,
    ),
    Window(
        Const("Выберите группу:"),
        Column(
            Select(
                text=Format("{item[name]}"),
                id="group_select",
                item_id_getter=lambda x: x["id"],
                items="groups",
                on_click=on_group_selected,
            )
        ),
        back_button,
        state=AddScheduleSG.group,
        getter=get_groups,
    ),
    Window(
        Const("Выберите пару:"),
        Column(
            Select(
                text=Format("{item[number]} | {item[start_at]} | {item[end_at]}"),
                id="class_select",
                item_id_getter=lambda x: x["id"],
                items="classes",
                on_click=on_class_selected,
            ),
        ),
        back_button,
        state=AddScheduleSG.class_,
        getter=get_classes,
    ),
    Window(
        Const("Выберите учебный предмет:"),
        ScrollingGroup(
            Select(
                text=Format("{item[name]}"),
                id="academic_subject_select",
                item_id_getter=lambda x: x["id"],
                items="academic_subjects",
                on_click=on_academic_subject_selected,
            ),
            id="academic_subjects_scroll",
            width=1,
            height=10,
        ),
        back_button,
        state=AddScheduleSG.academic_subject,
        getter=get_academic_subjects,
    ),
    Window(
        Const("Выберите тип пары:"),
        Column(
            Select(
                text=Format("{item[name]}"),
                id="class_type_select",
                item_id_getter=lambda x: x["id"],
                items="class_types",
                on_click=on_class_type_selected,
            ),
        ),
        back_button,
        state=AddScheduleSG.class_type,
        getter=get_class_types,
    ),
    Window(
        Const("Выберите аудиторию:"),
        Column(
            Select(
                text=Format("{item[name]}"),
                id="audience_select",
                item_id_getter=lambda x: x["id"],
                items="audiences",
                on_click=on_audience_selected,
            ),
        ),
        back_button,
        state=AddScheduleSG.audience,
        getter=get_audiences,
    ),
)
