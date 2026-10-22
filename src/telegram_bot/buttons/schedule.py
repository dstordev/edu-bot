from datetime import date

from aiogram.types import InlineKeyboardButton

from telegram_bot.utils.text_format import strike
from utils.datetime_format import DATE_FORMAT, RU_WEEKDAY_NAMES


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
    return InlineKeyboardButton(text=text, callback_data=f"class_schedule:day:{format_date}")
