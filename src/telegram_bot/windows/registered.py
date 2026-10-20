from datetime import time

from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models.tables import ReplacementSchedule, Schedule
from metadata import VERSION
from telegram_bot.buttons.homework import homework_menu_b
from telegram_bot.buttons.other import admin_menu_b, ranepa_b, student_settings_b
from telegram_bot.buttons.schedule import class_schedule_b
from telegram_bot.utils.html_format import b, blockquote, code
from telegram_bot.windows.info_window import InfoWindow
from utils.datetime_format import TIME_FORMAT


def start_window(is_admin: bool):
    builder = InlineKeyboardBuilder()
    builder.add(class_schedule_b, homework_menu_b, ranepa_b, student_settings_b)
    if is_admin:
        builder.add(admin_menu_b)
    builder.adjust(1)

    return InfoWindow(
        b("😼 Учебный помощник\n") + blockquote(f"Версия: v{VERSION}"), builder.as_markup()
    )


def notification_start_at_window(
    class_number: int,
    academic_subject_name: str,
    class_start_at: time,
    audience_name: str | None,
):
    format_class_start_at = format(class_start_at, TIME_FORMAT)
    return InfoWindow(
        b(
            "⏰ Через 5 минут начало занятия\n\n"
            f"👩‍🎓 №{class_number} {academic_subject_name} — с {code(format_class_start_at)} ({audience_name or 'Ауд. не указана'})"
        )
    )


def notification_end_at_window(
    class_number: int,
    academic_subject_name: str,
    class_end_at: time,
    audience_name: str | None,
    next_schedule: ReplacementSchedule | Schedule | None = None,
):
    format_class_end_at = format(class_end_at, TIME_FORMAT)
    text = b(
        "⏰ Через 5 минут конец занятия\n\n"
        f"👩‍🎓 №{class_number} {academic_subject_name} — до {code(format_class_end_at)} ({audience_name or 'Ауд. не указана'})"
    )
    if next_schedule:
        format_next_schedule_class_start_at = format(next_schedule.class_.start_at, TIME_FORMAT)
        text += (
            f"\n\n➡️ Следующая:\n"
            f"📚 №{next_schedule.class_.number} {next_schedule.academic_subject.name} — с {format_next_schedule_class_start_at} ({next_schedule.audience.name if next_schedule.audience else 'Ауд. не указана'})"
        )

    return InfoWindow(text)
