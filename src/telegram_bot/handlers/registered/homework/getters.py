from typing import Any

from aiogram.enums import ContentType
from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import MediaAttachment, MediaId

from db.repositories import DBRepositories
from telegram_bot.buttons.homework import homework_b
from telegram_bot.utils.html_format import b

from .help import format_homework_detail, get_student_info


async def get_homework_list_data(
    dialog_manager: DialogManager, dbrepositories: DBRepositories, **kwargs: Any
) -> dict[str, Any]:
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
    dialog_manager: DialogManager, dbrepositories: DBRepositories, **kwargs: Any
) -> dict[str, Any]:
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
