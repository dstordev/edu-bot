from collections.abc import Sequence
from datetime import datetime

from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models.tables import Student, Survey, SurveyData
from telegram_bot.buttons.other import back_b
from telegram_bot.buttons.presence import (
    absent_for_a_good_reason_b,
    not_on_site_b,
    on_site_b,
    presence_b,
    presence_surveys_b,
    survey_b,
)
from telegram_bot.utils.html_format import b, code
from telegram_bot.windows.info_window import InfoWindow
from utils.datetime_format import DATE_FORMAT, TIME_FORMAT


def presence_surveys_window(data: Sequence[Survey]):
    builder = InlineKeyboardBuilder()
    for survey in data:
        builder.add(survey_b(survey.id, survey.created_at))
    builder.add(back_b(presence_b))
    builder.adjust(1)

    return InfoWindow(b("📚 Опросы присутствия"), builder.as_markup())


def survey_window(survey_id: int, surveys_data: list[tuple[SurveyData, Student]]):
    states = {1: "✔️", 2: "✖️", 3: "🤒"}
    students_data_list: list[str] = []
    for id, (survey_data, student) in enumerate(surveys_data, 1):
        students_data_list.append(
            f"{id}. {student.surname} {student.name} {student.patronymic} {states[survey_data.state]}"
        )

    builder = InlineKeyboardBuilder()
    builder.add(back_b(presence_surveys_b))
    return InfoWindow(
        b(f"📖 На опросе №{survey_id} отметили присутствие:\n\n")
        + f"{'\n'.join(students_data_list)}",
        builder.as_markup(),
    )


def presence_check_window(survey_id: int, created_at: datetime):
    date_format = format(created_at, DATE_FORMAT)
    time_format = format(created_at, TIME_FORMAT)

    builder = InlineKeyboardBuilder()
    builder.add(
        on_site_b(survey_id),
        not_on_site_b(survey_id),
        absent_for_a_good_reason_b(survey_id),
    )
    builder.adjust(2, 1)

    return InfoWindow(
        b(
            f"🐱 Давай отметим твоё присутствие в опросе # {survey_id} {code(date_format)} {code(time_format)}:"
        ),
        builder.as_markup(),
    )


def presence_check_complete_window(survey_id: int):
    return InfoWindow(b(f"✔️ Успешно отметил твоё присутствие в опросе # {survey_id}"))
