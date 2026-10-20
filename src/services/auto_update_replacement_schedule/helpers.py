from datetime import date

from db.models.tables import ReplacementSchedule, Schedule
from telegram_bot.utils.html_format import b, code
from utils.datetime_format import DATE_FORMAT, RU_WEEKDAY_NAMES, TIME_FORMAT


def process_text_daily_schedule(
    class_schedule: list[Schedule | ReplacementSchedule], day: date, weekday: int
) -> str:
    schedule_text_lines = []
    for class_info in class_schedule:
        class_start_at: str = format(class_info.class_.start_at, TIME_FORMAT)
        class_end_at: str = format(class_info.class_.end_at, TIME_FORMAT)

        schedule_text_lines.append(
            f"{b(class_info.class_.number)}. {code(class_start_at)} - {code(class_end_at)} | "
            f"{class_info.academic_subject.name} | "
            f"{class_info.audience.name if class_info.audience else 'Ауд. не указана'} | "
            f"{class_info.class_type_.name if class_info.class_type_ else 'Тип не указан'}"
        )

    formatted_date = format(day, DATE_FORMAT)
    return (
        f"{b(f'📅 Расписание на {RU_WEEKDAY_NAMES[weekday]} {formatted_date}')}\n\n"
        f"{'\n'.join(schedule_text_lines)}"
    )
