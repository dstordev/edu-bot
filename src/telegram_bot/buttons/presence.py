from datetime import datetime

from aiogram.types import InlineKeyboardButton

from utils.datetime_format import DATE_FORMAT, TIME_FORMAT

presence_b = InlineKeyboardButton(text="📖 Присутствие", callback_data="presence")

presence_surveys_b = InlineKeyboardButton(
    text="📚 Опросы присутствия", callback_data="presence_surveys"
)

launch_presence_survey_b = InlineKeyboardButton(
    text="▶️ Запустить опрос присутствия", callback_data="launch_presence_survey"
)


def survey_b(survey_id: int, created_at: datetime) -> InlineKeyboardButton:
    date_format = format(created_at, DATE_FORMAT)
    time_format = format(created_at, TIME_FORMAT)

    return InlineKeyboardButton(
        text=f"№ {survey_id} | {date_format} {time_format}",
        callback_data=f"survey_id:{survey_id}",
    )


def on_site_b(survey_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(text="✔️ На месте", callback_data=f"on_site:{survey_id}")


def not_on_site_b(survey_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="✖️ Нет на месте", callback_data=f"not_on_site:{survey_id}"
    )


def absent_for_a_good_reason_b(survey_id: int) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text="🤒 Нет на месте по УП",
        callback_data=f"absent_for_a_good_reason:{survey_id}",
    )
