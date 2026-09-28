from datetime import datetime, date

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import ManagedTextInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Column, Select
from aiogram_dialog.widgets.text import Const, Format
from loguru import logger

from db.repositories import DBRepositories

add_replacement_schedule_router = Router()


class AddScheduleSG(StatesGroup):
    date = State()  # Дата пары
    group = State()  # Группа пары
    class_ = State()  # Номер пары
    academic_subject = State()  # Учебный предмет
    class_type = State()  # Тип пары (лекция, практика)
    audience = State()  # Аудитория


async def on_cancel(callback: CallbackQuery, button: Button, manager: DialogManager):
    """Обработчик отмены диалога."""

    await callback.answer("Отменено")
    await callback.message.delete()
    await manager.done()


# === Геттеры ===
async def get_groups(dbrepositories: DBRepositories, **kwargs):
    """Геттер для получения групп."""

    groups = await dbrepositories.group.get_groups()
    return {
        "groups": [
            {
                "id": str(group.id),
                "name": group.name,
            }
            for group in groups
        ],
    }


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


async def get_academic_subjects(dbrepositories: DBRepositories, **kwargs):
    """Геттер для получения учебных предметов."""

    academic_subjects = await dbrepositories.academic_subject.get_all(limit=20)
    return {
        "academic_subjects": [
            {"id": academic_subject.id, "name": academic_subject.name}
            for academic_subject in academic_subjects
        ]
    }


async def get_class_types(dbrepositories: DBRepositories, **kwargs):
    """Геттер для получения типов пар."""

    class_types = await dbrepositories.class_type.get_all()
    return {
        "class_types": [
            {
                "id": class_type.id,
                "name": class_type.name,
            }
            for class_type in class_types
        ]
    }


async def get_audiences(dbrepositories: DBRepositories, **kwargs):
    """Геттер для получения аудиторий."""

    audiences = await dbrepositories.audience.get_all()
    return {
        "audiences": [
            {
                "id": audience.id,
                "name": audience.name,
            }
            for audience in audiences
        ],
    }


# === Обработчики ===
async def on_date(
    message: Message, widget: ManagedTextInput[str], manager: DialogManager, data: str
):
    """Обработчик ввода даты."""

    try:
        # TODO: исправить предупреждение ruff о timezone
        datetime.strptime(data, "%d.%m.%Y").date()
    except Exception as ex:
        return logger.warning(f"Не удалось спарсить введенную дату: {ex}")

    manager.dialog_data["date"] = data
    await manager.next()


async def on_group_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    """Обработчик выбора группы."""

    manager.dialog_data["group"] = item_id
    await manager.next()


async def on_class_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    """Обработчик выбора пары."""

    manager.dialog_data["class_"] = item_id
    await manager.next()


async def on_academic_subject_selected(
    callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    """Обработчик выбора учебного предмета."""

    manager.dialog_data["academic_subject"] = item_id
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
    date_ = datetime.strptime(manager.dialog_data["date"], "%d.%m.%Y").date()
    group_id = int(manager.dialog_data["group"])
    class_id = int(manager.dialog_data["class_"])
    academic_subject_id = int(manager.dialog_data["academic_subject"])
    class_type_id = int(manager.dialog_data["class_type"])
    audience_id = int(item_id)

    r = await dbrepositories.replacement_schedule.add(
        date_, group_id, class_id, academic_subject_id, class_type_id, audience_id
    )

    await callback.message.edit_text(f"Пара добавлена, id: {r.id}")
    await manager.done()


add_schedule_dialog = Dialog(
    Window(
        Const("Введите дату (формат дд.мм.гггг):"),
        Button(Const("Отменить"), id="cancel", on_click=on_cancel),
        TextInput(
            id="date_input",
            on_success=on_date,
        ),
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
        state=AddScheduleSG.class_,
        getter=get_classes,
    ),
    Window(
        Const("Выберите учебный предмет:"),
        Column(
            Select(
                text=Format("{item[name]}"),
                id="academic_subject_select",
                item_id_getter=lambda x: x["id"],
                items="academic_subjects",
                on_click=on_academic_subject_selected,
            ),
        ),
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
        state=AddScheduleSG.audience,
        getter=get_audiences,
    ),
)


@add_replacement_schedule_router.message(Command("add_replacement_schedule"))
async def start_add(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(AddScheduleSG.date, mode=StartMode.RESET_STACK)


add_replacement_schedule_router.include_router(add_schedule_dialog)
