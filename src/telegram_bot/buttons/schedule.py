from datetime import date

from aiogram.enums.button_style import ButtonStyle
from aiogram.types import InlineKeyboardButton

from telegram_bot.utils.text_format import strike
from utils.datetime_format import DATE_FORMAT, RU_WEEKDAY_NAMES

class_schedule_b = InlineKeyboardButton(
    text="🗓️ Расписание", callback_data="class_schedule", style=ButtonStyle.PRIMARY
)

class_schedule_today_b = InlineKeyboardButton(
    text="Сегодня",
    callback_data="class_schedule:day:today",
    style=ButtonStyle.PRIMARY,
)
class_schedule_tomorrow_b = InlineKeyboardButton(
    text="Завтра",
    callback_data="class_schedule:day:tomorrow",
    style=ButtonStyle.PRIMARY,
)
class_schedule_current_week_b = InlineKeyboardButton(
    text="📅 Текущая неделя", callback_data="class_schedule:week:current_week"
)
class_schedule_next_week_b = InlineKeyboardButton(
    text="📅 Следующая неделя", callback_data="class_schedule:week:next_week"
)


def class_schedule_onday_b(
    date_: date, *, current_day: bool = False, strikethrough: bool = False
) -> InlineKeyboardButton:
    week_day_name = RU_WEEKDAY_NAMES[date_.weekday()]
    if strikethrough:
        week_day_name = strike(week_day_name)

    text = f"⚪ {week_day_name}"
    if current_day:
        text = f"🟢 {week_day_name}"

    format_date = format(date_, DATE_FORMAT)
    return InlineKeyboardButton(
        text=text, callback_data=f"class_schedule:day:{format_date}"
    )
