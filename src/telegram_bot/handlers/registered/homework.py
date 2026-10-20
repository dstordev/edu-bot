from typing import Any

from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InputMediaDocument,
    InputMediaPhoto,
    MediaUnion,
)
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.kbd import Button, Column, Row, Select, SwitchTo
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from db.models.tables import Homework
from db.repositories import DBRepositories
from telegram_bot.buttons.homework import (
    homework_b,
    homework_finished_b,
    homework_menu_b,
    homework_unfinished_b,
)
from telegram_bot.handlers.registered.general import (
    command_start_handler_registered,
)
from telegram_bot.utils.html_format import b, blockquote
from utils.datetime_format import DATE_FORMAT

registered_homework_router = Router(name=__name__)


class HomeworkSG(StatesGroup):
    menu = State()  # Меню выбора: выполненные / невыполненные
    list = State()  # Универсальный список заданий с пагинацией
    detail = State()  # Просмотр конкретного задания


# --- Вспомогательные функции ---


async def get_student_info(manager: DialogManager, repos: DBRepositories) -> tuple[int, int]:
    """Кэширует student_id и group_id в рамках диалога."""
    if "student_id" not in manager.dialog_data:
        student = await repos.student.find_by_telegram_id(manager.event.from_user.id)
        assert student is not None
        manager.dialog_data["student_id"] = student.id
        manager.dialog_data["group_id"] = student.group_id
    return manager.dialog_data["student_id"], manager.dialog_data["group_id"]


def format_homework_detail(homework: Homework) -> str:
    lines = [f"{b('📌 Домашнее задание')}"]
    if homework.assignment_date:
        lines.append(f"— Дата назначения: {format(homework.assignment_date, DATE_FORMAT)}")
    lines.append(f"— Предмет: {homework.academic_subject.name}\n")
    lines.append(blockquote(homework.text))
    return "\n".join(lines)


# --- Точка входа ---


@registered_homework_router.callback_query(F.data == homework_menu_b.callback_data)
async def handler_homework_menu(event: CallbackQuery, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(HomeworkSG.menu, mode=StartMode.RESET_STACK)


# --- Обработчики действий ---


async def on_back_to_main_menu(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    state = manager.middleware_data["state"]
    await command_start_handler_registered(callback, state, manager)


async def on_open_list(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    """Проверяет наличие заданий перед переходом в список."""
    repos: DBRepositories = manager.middleware_data["dbrepositories"]
    student_id, group_id = await get_student_info(manager, repos)
    hw_type = button.widget_id  # 'unfinished' или 'finished'

    if hw_type == "unfinished":
        items = await repos.homework.get_unfinished_homeworks(student_id, group_id, page_index=0)
        empty_msg = "🐈 Здесь нет невыполненных заданий"
    else:
        items = await repos.homework.get_finished_homeworks(student_id, page_index=0)
        empty_msg = "🐈 Здесь нет выполненных заданий"

    if not items:
        await callback.answer(empty_msg, show_alert=True)
        return

    manager.dialog_data["hw_type"] = hw_type
    manager.dialog_data["page"] = 0
    await manager.switch_to(HomeworkSG.list)


async def on_change_page(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    """Листает страницы пагинации вперед/назад с проверкой."""
    repos: DBRepositories = manager.middleware_data["dbrepositories"]
    student_id, group_id = await get_student_info(manager, repos)
    hw_type = manager.dialog_data["hw_type"]
    current_page: int = manager.dialog_data.get("page", 0)

    if button.widget_id == "prev_page":
        if current_page > 0:
            manager.dialog_data["page"] = current_page - 1
        return

    # Если нажали "Вперед" — проверяем, есть ли что-то на следующей странице
    next_page = current_page + 1
    if hw_type == "unfinished":
        items = await repos.homework.get_unfinished_homeworks(
            student_id, group_id, page_index=next_page
        )
    else:
        items = await repos.homework.get_finished_homeworks(student_id, page_index=next_page)

    if not items:
        await callback.answer("🐈 Больше заданий нет", show_alert=True)
        return

    manager.dialog_data["page"] = next_page


async def on_homework_select(
    callback: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
) -> None:
    manager.dialog_data["current_hw_id"] = int(item_id)
    await manager.switch_to(HomeworkSG.detail)


async def on_complete_homework(
    callback: CallbackQuery, button: Button, manager: DialogManager
) -> None:
    repos: DBRepositories = manager.middleware_data["dbrepositories"]
    student_id, _ = await get_student_info(manager, repos)
    hw_id = manager.dialog_data["current_hw_id"]

    await repos.student_homework.mark_completed(student_id=student_id, homework_id=hw_id)
    await callback.answer("✅ Отметил домашнее задание как выполненное", show_alert=True)

    # Возврат в меню ДЗ
    await manager.switch_to(HomeworkSG.menu)


async def on_view_files(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    """Отправляет все прикрепленные медиафайлы альбомом."""
    if not callback.message:
        return

    repos: DBRepositories = manager.middleware_data["dbrepositories"]
    hw_id = manager.dialog_data["current_hw_id"]
    homework = await repos.homework.get_homework(hw_id)
    assert homework is not None

    caption = b(f"📑 Материал к домашнему заданию {homework.id}")

    if homework.homework_photo:
        photos: list[MediaUnion] = [
            InputMediaPhoto(media=i.telegram_file_id) for i in homework.homework_photo[:-1]
        ]
        photos.append(
            InputMediaPhoto(
                media=homework.homework_photo[-1].telegram_file_id,
                caption=caption,
            )
        )
        await callback.message.answer_media_group(photos)

    if homework.homework_file:
        files: list[MediaUnion] = [
            InputMediaDocument(media=i.telegram_file_id) for i in homework.homework_file[:-1]
        ]
        files.append(
            InputMediaDocument(
                media=homework.homework_file[-1].telegram_file_id,
                caption=caption,
            )
        )
        await callback.message.answer_media_group(files)

    await callback.answer()


# --- Геттеры данных ---


async def get_homework_list_data(
    dialog_manager: DialogManager, dbrepositories: DBRepositories, **kwargs
) -> dict:
    student_id, group_id = await get_student_info(dialog_manager, dbrepositories)
    hw_type = dialog_manager.dialog_data.get("hw_type", "unfinished")
    page_index = dialog_manager.dialog_data.get("page", 0)

    if hw_type == "unfinished":
        title = b("🟠 Ваши невыполненные задания:")
        homeworks = await dbrepositories.homework.get_unfinished_homeworks(
            student_id, group_id, page_index=page_index
        )
    else:
        title = b("🟢 Ваши выполненные задания:")
        homeworks = await dbrepositories.homework.get_finished_homeworks(
            student_id, page_index=page_index
        )

    # Формируем элементы для Select
    items = [
        {
            "id": str(hw.id),
            "title": homework_b(
                homework_id=hw.id, homework_academic_subject=hw.academic_subject
            ).text,
        }
        for hw in homeworks
    ]

    return {
        "list_title": title,
        "homeworks": items,
        "has_prev": page_index > 0,
    }


async def get_homework_detail_data(
    dialog_manager: DialogManager, dbrepositories: DBRepositories, **kwargs
) -> dict:
    student_id, _ = await get_student_info(dialog_manager, dbrepositories)
    hw_id = dialog_manager.dialog_data["current_hw_id"]

    homework = await dbrepositories.homework.get_homework(hw_id)
    assert homework is not None

    is_finished = await dbrepositories.homework.is_finished_homework(
        student_id=student_id, homework_id=hw_id
    )

    # Прикрепление первого медиа к самому сообщению диалога
    media = None
    if homework.homework_photo:
        media = MediaAttachment(
            type=ContentType.PHOTO,
            file_id=MediaId(homework.homework_photo[0].telegram_file_id),
        )
    elif homework.homework_file:
        media = MediaAttachment(
            type=ContentType.DOCUMENT,
            file_id=MediaId(homework.homework_file[0].telegram_file_id),
        )

    total_files = len(homework.homework_photo) + len(homework.homework_file)

    return {
        "detail_text": format_homework_detail(homework),
        "media": media,
        "has_media": media is not None,
        "can_complete": not is_finished,
        "has_additional_material": total_files > 1,
    }


# --- Диалог ---

dialog = Dialog(
    # 1. Меню ДЗ
    Window(
        Const(b(homework_menu_b.text)),
        Button(
            Const(homework_unfinished_b().text),
            id="unfinished",
            on_click=on_open_list,
        ),
        Button(
            Const(homework_finished_b().text),
            id="finished",
            on_click=on_open_list,
        ),
        Button(Const("◀️ Главное меню"), id="to_menu", on_click=on_back_to_main_menu),
        state=HomeworkSG.menu,
    ),
    # 2. Список заданий
    Window(
        Format("{list_title}"),
        Column(
            Select(
                Format("{item[title]}"),
                id="select_hw",
                item_id_getter=lambda item: item["id"],
                items="homeworks",
                on_click=on_homework_select,
            )
        ),
        Row(
            Button(
                Const("⬅️ Предыдущая"),
                id="prev_page",
                on_click=on_change_page,
                when="has_prev",
            ),
            Button(
                Const("Следующая ➡️"),
                id="next_page",
                on_click=on_change_page,
            ),
        ),
        SwitchTo(Const("◀️ Назад"), id="back_to_menu", state=HomeworkSG.menu),
        state=HomeworkSG.list,
        getter=get_homework_list_data,
    ),
    # 3. Детальный просмотр задания
    Window(
        DynamicMedia("media", when="has_media"),
        Format("{detail_text}"),
        Button(
            Const("📑 Материалы к заданию"),
            id="view_files",
            on_click=on_view_files,
            when="has_additional_material",
        ),
        Button(
            Const("✅ Отметить выполненным"),
            id="complete_hw",
            on_click=on_complete_homework,
            when="can_complete",
        ),
        SwitchTo(Const("◀️ Назад"), id="back_to_list", state=HomeworkSG.list),
        state=HomeworkSG.detail,
        getter=get_homework_detail_data,
    ),
)

registered_homework_router.include_routers(dialog)
