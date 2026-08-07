from datetime import UTC, datetime, timedelta

from aiogram import F, Router
from aiogram.types import CallbackQuery
from loguru import logger

from db.repositories import DBRepositories
from db.services.schedule import get_daily_schedule, get_weekly_schedule
from db.services.working_days import is_non_working_day
from telegram_bot.buttons.schedule import (
    class_schedule_b,
    class_schedule_current_week_b,
    class_schedule_next_week_b,
)
from telegram_bot.windows.registered import class_schedule_window
from telegram_bot.windows.schedule import (
    CurrentWeeklyScheduleWindow,
    DailyScheduleWindow,
    NextWeeklyScheduleWindow,
)
from utils.datetime_format import DATE_FORMAT

registered_schedule_router = Router(name=__name__)


@registered_schedule_router.callback_query(F.data == class_schedule_b.callback_data)
async def handler_class_schedule_b(event: CallbackQuery):
    await class_schedule_window().answer_window(event)


@registered_schedule_router.callback_query(F.data.startswith("class_schedule:day:"))
async def handler_class_schedule_day(
    event: CallbackQuery, dbrepositories: DBRepositories
):
    assert event.data is not None
    cb_data = event.data.split(":")
    assert len(cb_data) == 3
    selected_day = cb_data[2]

    now_day = datetime.now(UTC).astimezone().date()
    if selected_day == "today":
        target_day = now_day
    elif selected_day == "tomorrow":
        target_day = now_day + timedelta(days=1)
    else:
        target_day = datetime.strptime(selected_day, DATE_FORMAT).date()

    student = await dbrepositories.student.find_by_telegram_id(event.from_user.id)
    assert student is not None

    # Проверка учебного дня
    non_working_day = await is_non_working_day(
        day=target_day, dbrepositories=dbrepositories
    )
    if non_working_day is True:
        logger.info(
            f"Не показываю расписание на {target_day} так как это нерабочий день."
        )
        await event.answer("🐱 Это неучебный день", show_alert=True)
        return

    # Получение расписания на день
    daily_schedule = await get_daily_schedule(
        student.group_id, target_day, dbrepositories
    )

    # Если расписание не установлено
    if len(daily_schedule.classes) == 0:
        logger.info(
            f"Не показываю расписание на {target_day} так как оно не установлено."
        )
        await event.answer("🐱 На этот день не установлено расписание", show_alert=True)
        return

    current_week = target_day.isocalendar().week == now_day.isocalendar().week
    next_week = (
        target_day.isocalendar().week
        == (now_day + timedelta(weeks=1)).isocalendar().week
    )

    back_btn = None
    if current_week is True:
        back_btn = class_schedule_current_week_b
    elif next_week is True:
        back_btn = class_schedule_next_week_b

    # Создание окна с расписанием на день
    daily_schedule_window = DailyScheduleWindow(
        class_schedule=daily_schedule.classes,
        day=daily_schedule.day_date,
        weekday=daily_schedule.weekday_number,
        back_btn=back_btn,
    )

    await daily_schedule_window.answer_window(event)


@registered_schedule_router.callback_query(F.data.startswith("class_schedule:week:"))
async def handler_class_schedule_week(
    event: CallbackQuery, dbrepositories: DBRepositories
):
    selected_week = event.data.split(":")[2]  # pyright: ignore[reportOptionalMemberAccess]

    now_day = datetime.now(UTC).astimezone().date()
    if selected_week == "current_week":
        helper_day = now_day
    elif selected_week == "next_week":
        helper_day = now_day + timedelta(weeks=1)
    else:
        return logger.warning(f"Неизвестный selected week: {selected_week}")

    student = await dbrepositories.student.find_by_telegram_id(event.from_user.id)

    # Получение расписания на неделю
    weekly_schedule = await get_weekly_schedule(
        student.group_id,  # pyright: ignore[reportOptionalMemberAccess]
        helper_day,
        dbrepositories,
    )

    # Создание окна с расписанием на неделю
    if selected_week == "current_week":
        weekly_schedule_window = CurrentWeeklyScheduleWindow(
            week_days=weekly_schedule.week_days,
            week_stars="*" if weekly_schedule.week_stars == 1 else "**",
        )
    elif selected_week == "next_week":
        weekly_schedule_window = NextWeeklyScheduleWindow(
            week_days=weekly_schedule.week_days,
            week_stars="*" if weekly_schedule.week_stars == 1 else "**",
        )

    await weekly_schedule_window.answer_window(event)  # pyright: ignore[reportPossiblyUnboundVariable]
