import asyncio

from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from db.repositories import DBRepositories
from telegram_bot.buttons.presence import launch_presence_survey_b, presence_b
from telegram_bot.filters import IsAdminFilter
from telegram_bot.utils.html_format import b
from telegram_bot.windows.presence import presence_check_window
from telegram_bot.windows.registered import presence_window

admin_presence_router = Router()


@admin_presence_router.callback_query(F.data == presence_b.callback_data)
async def presence_handler(event: CallbackQuery) -> None:
    await presence_window(True).answer_window(event)


@admin_presence_router.callback_query(
    F.data == launch_presence_survey_b.callback_data, IsAdminFilter()
)
async def launch_presence_survey_handler(
    event: CallbackQuery, dbrepositories: DBRepositories
) -> None:
    if event.bot is None:
        return logger.warning("Не удалось получить объект `bot` из объекта event.")
    if event.message is None:
        return logger.warning("Объект `Message` не ожидается как None.")

    survey = await dbrepositories.survey.create()
    window = presence_check_window(survey.id, survey.created_at.astimezone())
    group_data = await dbrepositories.group.find_by_name("25-Ф-12с")
    if group_data is None:
        return logger.warning("Не удалось найти группу в БД.")

    await event.answer(f"🕐 Начинаю опрос присутствия № {survey.id}", show_alert=True)

    count_successful = 0
    errors = 0

    async for student in dbrepositories.student.find_students_by_group(group_data.id):
        await asyncio.sleep(0.5)
        try:
            await window.send_window(event.bot, student.telegram_id)
            count_successful += 1
        except Exception as _ex:
            logger.exception(
                "Во время рассылки при попытке отравить сообщение пользователю возникла неизвестная ошибка.",
                _ex,
            )
            errors += 1

    await event.message.answer(
        b(
            f"🐱 Рассылка опроса присутствия № {survey.id} окончена.\n"
            f"- ✔️ Кол-во успешно отправленных сообщений: {count_successful}\n"
            f"- ✖️ Кол-во ошибок при отправке сообщений: {errors}"
        )
    )
