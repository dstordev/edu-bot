from datetime import time

from db.models.tables import ReplacementSchedule, Schedule
from telegram_bot.utils.html_format import b, code
from utils.datetime_format import TIME_FORMAT


def process_text_notification_start_at(
    lesson_num: int,
    academic_subject_name: str,
    lesson_start_at: time,
    audience_name: str | None = None,
) -> str:
    lesson_start_at_format = format(lesson_start_at, TIME_FORMAT)
    return b(
        "⏰ Через 5 минут начало занятия\n\n"
        f"👩‍🎓 №{lesson_num} {academic_subject_name} — с {code(lesson_start_at_format)} "
        f"({audience_name or 'Ауд. не указана'})"
    )


def process_text_notification_end_at(
    lesson_num: int,
    academic_subject_name: str,
    lesson_end_at: time,
    audience_name: str | None = None,
    next_schedule: ReplacementSchedule | Schedule | None = None,
) -> str:
    lesson_end_at_format = format(lesson_end_at, TIME_FORMAT)
    text = b(
        "⏰ Через 5 минут конец занятия\n\n"
        f"👩‍🎓 №{lesson_num} {academic_subject_name} — до {code(lesson_end_at_format)} "
        f"({audience_name or 'Ауд. не указана'})"
    )
    if next_schedule:
        next_schedule_lesson_start_at_format = format(next_schedule.class_.start_at, TIME_FORMAT)
        text += (
            f"\n\n➡️ Следующая:\n"
            f"📚 №{next_schedule.class_.number} {next_schedule.academic_subject.name} — с "
            f"{next_schedule_lesson_start_at_format} "
            f"({next_schedule.audience.name if next_schedule.audience else 'Ауд. не указана'})"
        )

    return text
