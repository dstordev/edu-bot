from aiogram import F, Router
from aiogram.types import CallbackQuery, InaccessibleMessage
from loguru import logger

from db.models.tables import Student, SurveyData
from db.repositories import DBRepositories
from enums import SurveyState
from telegram_bot.buttons.presence import presence_b, presence_surveys_b
from telegram_bot.windows.presence import (
    presence_check_complete_window,
    presence_surveys_window,
    survey_window,
)
from telegram_bot.windows.registered import presence_window

registered_presence_router = Router()


@registered_presence_router.callback_query(F.data == presence_b.callback_data)
async def callback_presence_handler(event: CallbackQuery) -> None:
    await presence_window(False).answer_window(event)


@registered_presence_router.callback_query(F.data == presence_surveys_b.callback_data)
async def callback_presence_surveys_handler(
    event: CallbackQuery, dbrepositories: DBRepositories
) -> None:
    surveys = await dbrepositories.survey.get_surveys()

    # Перед отображением времени переводим его в локальную зону
    for survey in surveys:
        survey.created_at = survey.created_at.astimezone()
    await presence_surveys_window(surveys).answer_window(event)


@registered_presence_router.callback_query(F.data.startswith("survey_id:"))
async def callback_survey_id_handler(
    event: CallbackQuery, dbrepositories: DBRepositories
) -> None:
    survey_id = int(
        event.data.split(":")[-1]  # pyright: ignore[reportOptionalMemberAccess]
    )
    data: list[tuple[SurveyData, Student]] = []

    students_tags_in_survey = (
        await dbrepositories.survey_data.find_students_tags_in_survey(survey_id)
    )
    for tag in students_tags_in_survey:
        if student_data := await dbrepositories.student.find(tag.student_id):
            data.append((tag, student_data))

    await survey_window(survey_id, data).answer_window(event)


@registered_presence_router.callback_query(F.data.startswith("on_site:"))
@registered_presence_router.callback_query(F.data.startswith("not_on_site:"))
@registered_presence_router.callback_query(
    F.data.startswith("absent_for_a_good_reason:")
)
async def callback_check_answer_survey(
    event: CallbackQuery, dbrepositories: DBRepositories
):
    if event.message is None or isinstance(event.message, InaccessibleMessage):
        return logger.warning(
            "Объект `Message` не ожидается как None или InaccessibleMessage"
        )

    callback_data, survey_id = event.data.split(":")  # pyright: ignore[reportOptionalMemberAccess]

    states = {
        "on_site": SurveyState.on_site,
        "not_on_site": SurveyState.not_on_site,
        "absent_for_a_good_reason": SurveyState.absent_for_a_good_reason,
    }

    student = await dbrepositories.student.find_by_telegram_id(event.from_user.id)
    if not student:
        return logger.warning("Не удалось найти студента по telegram_id")

    await dbrepositories.survey_data.tag_student_in_survey(
        survey_id=int(survey_id),
        student_id=int(student.id),
        state=states[callback_data],
    )

    await event.answer("✔️ Успешно отметил твоё присутствие", show_alert=True)
    await presence_check_complete_window(int(survey_id)).answer_window(event)
