from typing import Any

from aiogram.types import CallbackQuery, InputMediaDocument, InputMediaPhoto, MediaUnion
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button

from db.repositories import DBRepositories
from telegram_bot.utils.html_format import b

from .help import get_student_info
from .states import HomeworkSG


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
        manager.show_mode = ShowMode.SEND
        await callback.answer()

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
        manager.show_mode = ShowMode.SEND
        await callback.answer()

    await callback.answer()
