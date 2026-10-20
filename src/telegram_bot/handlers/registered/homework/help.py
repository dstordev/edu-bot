from aiogram_dialog import DialogManager

from db.models.tables import Homework
from db.repositories import DBRepositories
from telegram_bot.utils.html_format import b, blockquote
from utils.datetime_format import DATE_FORMAT


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
