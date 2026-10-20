from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models.tables import ReplacementSchedule, Schedule
from telegram_bot.buttons.other import back_b
from telegram_bot.buttons.schedule import class_schedule_b
from telegram_bot.utils.html_format import b, code
from telegram_bot.windows.info_window import InfoWindow
from utils.datetime_format import DATE_FORMAT, RU_WEEKDAY_NAMES, TIME_FORMAT


class DailyScheduleWindow(InfoWindow):
    def __init__(
        self,
        *,
        class_schedule: list[Schedule | ReplacementSchedule],
        day: date,
        weekday: int,
        back_btn: InlineKeyboardButton | None = None,
    ) -> None:
        self.back_btn = back_btn

        schedule_text_lines = []
        for class_info in class_schedule:
            class_start_at: str = format(class_info.class_.start_at, TIME_FORMAT)
            class_end_at: str = format(class_info.class_.end_at, TIME_FORMAT)

            schedule_text_lines.append(
                f"{b(class_info.class_.number)}. {code(class_start_at)} - {code(class_end_at)} | {class_info.academic_subject.name} | {class_info.audience.name if class_info.audience else 'Ауд. не указана'} | {class_info.class_type_.name if class_info.class_type_ else 'Тип не указан'}"
            )

        formatted_date = format(day, DATE_FORMAT)
        super().__init__(
            f"{b(f'📅 Расписание на {RU_WEEKDAY_NAMES[weekday]} {formatted_date}')}\n\n"
            f"{'\n'.join(schedule_text_lines)}",
            inline_keyboard_markup=self.inline_keyboard(),
        )

    def inline_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if self.back_btn is None:
            builder.add(back_b(class_schedule_b))
        else:
            builder.add(back_b(self.back_btn))
        return builder.as_markup()
