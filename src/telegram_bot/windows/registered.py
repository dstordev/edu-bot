from datetime import time

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models.tables import AcademicSubject, ReplacementSchedule, Schedule
from telegram_bot.buttons.homework import homework_menu_b
from telegram_bot.buttons.other import academic_subject_b, back_b, ranepa_b, start_b
from telegram_bot.buttons.presence import (
    launch_presence_survey_b,
    presence_surveys_b,
)
from telegram_bot.buttons.schedule import (
    class_schedule_b,
    class_schedule_current_week_b,
    class_schedule_next_week_b,
    class_schedule_today_b,
    class_schedule_tomorrow_b,
)
from telegram_bot.utils.html_format import b, code
from telegram_bot.windows.info_window import InfoWindow
from utils.datetime_format import TIME_FORMAT


def start_window():
    builder = InlineKeyboardBuilder()
    builder.add(class_schedule_b, homework_menu_b, ranepa_b)
    builder.adjust(1)

    return InfoWindow(b("😼 Учебный помощник"), builder.as_markup())


def presence_window(is_admin: bool):
    builder = InlineKeyboardBuilder()
    builder.add(presence_surveys_b)
    if is_admin:
        builder.add(launch_presence_survey_b)
    builder.add(back_b(start_b))
    builder.adjust(1)

    return InfoWindow(b("📖 Присутствие"), builder.as_markup())


def class_schedule_window():
    builder = InlineKeyboardBuilder()
    builder.add(
        class_schedule_current_week_b,
        class_schedule_next_week_b,
        class_schedule_today_b,
        class_schedule_tomorrow_b,
        back_b(start_b),
    )
    builder.adjust(1, 1, 2)

    return InfoWindow(f"{b('🗓️ Расписание')}", builder.as_markup())


def notification_start_at_window(
    class_number: int,
    academic_subject_name: str,
    class_start_at: time,
    audience_name: str,
):
    format_class_start_at = format(class_start_at, TIME_FORMAT)
    return InfoWindow(
        b(
            "⏰ Через 5 минут начало занятия\n\n"
            f"👩‍🎓 №{class_number} {academic_subject_name} — с {code(format_class_start_at)} ({audience_name})"
        )
    )


def notification_end_at_window(
    class_number: int,
    academic_subject_name: str,
    class_end_at: time,
    audience_name: str,
    next_schedule: ReplacementSchedule | Schedule | None = None,
):
    format_class_end_at = format(class_end_at, TIME_FORMAT)
    text = b(
        "⏰ Через 5 минут конец занятия\n\n"
        f"👩‍🎓 №{class_number} {academic_subject_name} — до {code(format_class_end_at)} ({audience_name})"
    )
    if next_schedule:
        format_next_schedule_class_start_at = format(
            next_schedule.class_.start_at, TIME_FORMAT
        )
        text += (
            f"\n\n➡️ Следующая:\n"
            f"📚 №{next_schedule.class_.number} {next_schedule.academic_subject.name} — с {format_next_schedule_class_start_at} ({next_schedule.audience.name})"
        )

    return InfoWindow(text)


# окошко с выбором предметов
def academic_subjects_window(
    *, academic_subjects: list[AcademicSubject], back_btn: InlineKeyboardButton
) -> InfoWindow:
    builder = InlineKeyboardBuilder()
    for academic_subject in academic_subjects:
        builder.add(
            academic_subject_b(
                name=academic_subject.name, academic_subject_id=academic_subject.id
            )
        )
    builder.add(back_b(back_btn))
    builder.adjust(1)

    return InfoWindow(b("📚 Учебные предметы:"), builder.as_markup())
