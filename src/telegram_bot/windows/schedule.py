from datetime import date
from typing import Literal

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models.tables import ReplacementSchedule, Schedule
from db.services.schedule import DailySchedule
from telegram_bot.buttons.other import back_b
from telegram_bot.buttons.schedule import class_schedule_b, class_schedule_onday_b
from telegram_bot.utils.html_format import b, code, i
from telegram_bot.windows.info_window import InfoWindow
from utils.datetime_format import DATE_FORMAT, RU_WEEKDAY_NAMES, TIME_FORMAT


class _WeeklyScheduleWindow(InfoWindow):
    def __init__(
        self, *, week_days: list[DailySchedule], week_stars: Literal["*", "**"]
    ):
        self.week_days = week_days
        super().__init__(
            text=(
                f"{b(f'📆 Расписание на неделю ({week_stars})')}\n\n"
                f"{i('🟢 - Текущий день.')}"
            ),
            inline_keyboard_markup=self.inline_keyboard(),
        )

    def inline_keyboard(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for week_day in self.week_days:
            builder.add(
                class_schedule_onday_b(
                    week_day.day_date,
                    current_day=week_day.is_current_day,
                    strikethrough=week_day.is_non_working_day,
                )
            )
        builder.add(back_b(class_schedule_b))
        builder.adjust(1)
        return builder.as_markup()


class CurrentWeeklyScheduleWindow(_WeeklyScheduleWindow):
    def __init__(
        self,
        *,
        week_days: list[DailySchedule],
        week_stars: Literal["*", "**"],
    ):
        super().__init__(week_days=week_days, week_stars=week_stars)
        self.text = (
            f"{b(f'📆 Расписание на текущую неделю ({week_stars})')}\n\n"
            f"{i('🟢 - Текущий день.')}"
        )


class NextWeeklyScheduleWindow(_WeeklyScheduleWindow):
    def __init__(
        self,
        *,
        week_days: list[DailySchedule],
        week_stars: Literal["*", "**"],
    ):
        super().__init__(week_days=week_days, week_stars=week_stars)
        self.text = f"{b(f'📆 Расписание на следующую неделю ({week_stars})')}"


class DailyScheduleWindow(InfoWindow):
    def __init__(
        self,
        *,
        class_schedule: list[Schedule | ReplacementSchedule],
        day: date,
        weekday: int,
        back_btn: InlineKeyboardButton | None = None,
    ):
        self.back_btn = back_btn

        schedule_text_lines = []
        for class_info in class_schedule:
            class_start_at: str = format(class_info.class_.start_at, TIME_FORMAT)
            class_end_at: str = format(class_info.class_.end_at, TIME_FORMAT)

            # 1. 08:30 - 10:00 | Ауд. не указана | Физкультура
            schedule_text_lines.append(
                f"{b(class_info.class_.number)}. {code(class_start_at)} - {code(class_end_at)} | {class_info.academic_subject.name} | {class_info.audience.name} | {class_info.class_type_.name}"
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
