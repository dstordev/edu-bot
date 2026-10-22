from datetime import date, datetime, timedelta
from typing import Any

from aiogram.enums import ButtonStyle
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Column, Row, Select
from aiogram_dialog.widgets.style import Style
from aiogram_dialog.widgets.text import Const, Format
from loguru import logger

from db.repositories import DBRepositories
from db.services.schedule import DailySchedule, get_daily_schedule, get_weekly_schedule
from db.services.working_days import is_non_working_day
from telegram_bot.buttons.schedule import (
    class_schedule_onday_b,
)
from telegram_bot.utils.html_format import b, code, i
from utils.datetime_format import DATE_FORMAT, RU_WEEKDAY_NAMES, TIME_FORMAT
from utils.timezones import TZ_MOSCOW


class ScheduleSG(StatesGroup):
    main = State()
    week_schedule = State()
    day_schedule = State()


# --- Вспомогательные функции ---


async def get_student_group_id(manager: DialogManager, repos: DBRepositories) -> int:
    """Кэширует group_id в рамках диалога, исключая повторные запросы в БД."""

    if "group_id" not in manager.dialog_data:
        student = await repos.student.find_by_telegram_id(manager.event.from_user.id)
        assert student is not None
        manager.dialog_data["group_id"] = student.group_id
    return manager.dialog_data["group_id"]


def parse_target_date(selected_day: str) -> date:
    today = datetime.now(TZ_MOSCOW).date()
    if selected_day == "today":
        return today
    if selected_day == "tomorrow":
        return today + timedelta(days=1)
    return datetime.strptime(selected_day, DATE_FORMAT).date()


def format_daily_schedule(daily_schedule: DailySchedule) -> str:
    lines = [
        f"{b(c.class_.number)}. {code(c.class_.start_at.strftime(TIME_FORMAT))} - "
        f"{code(c.class_.end_at.strftime(TIME_FORMAT))} | {c.academic_subject.name} | "
        f"{c.audience.name if c.audience else 'Ауд. не указана'} | "
        f"{c.class_type_.name if c.class_type_ else 'Тип не указан'}"
        for c in daily_schedule.classes
    ]
    weekday = RU_WEEKDAY_NAMES[daily_schedule.weekday_number]
    date_str = daily_schedule.day_date.strftime(DATE_FORMAT)
    return f"{b(f'📅 Расписание на {weekday} {date_str}')}\n\n" + "\n".join(lines)


# --- Обработчики действий ---


async def on_back_from_day(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    # Если пришли из недели — возвращаем в неделю, иначе — в главное меню
    if manager.dialog_data.get("day_opened_from") == "week":
        await manager.switch_to(ScheduleSG.week_schedule)
    else:
        await manager.switch_to(ScheduleSG.main)


async def on_week_schedule(callback: CallbackQuery, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["selected_week"] = button.widget_id
    await manager.switch_to(ScheduleSG.week_schedule)


async def on_day_schedule(
    callback: CallbackQuery,
    widget: Any,
    manager: DialogManager,
    item_id: str | None = None,
) -> None:
    """
    Универсальный хэндлер: работает и для Button ('today'/'tomorrow'),
    и для Select (конкретная дата).
    """

    selected_day = item_id or widget.widget_id
    repos: DBRepositories = manager.middleware_data["dbrepositories"]
    group_id = await get_student_group_id(manager, repos)
    target_day = parse_target_date(selected_day)

    # Валидации с показом всплывающего алерта
    if await is_non_working_day(group_id=group_id, day=target_day, dbrepositories=repos):
        logger.info(f"Неучебный день: {target_day}")
        await callback.answer("🐱 Это неучебный день", show_alert=True)
        return

    daily_schedule = await get_daily_schedule(group_id, target_day, repos)
    if not daily_schedule.classes:
        logger.info(f"Пустое расписание на {target_day}")
        await callback.answer("🐱 На этот день не установлено расписание", show_alert=True)
        return

    manager.dialog_data["day_opened_from"] = (
        "main" if manager.current_context().state == ScheduleSG.main else "week"
    )

    # Сохраняем уже готовый текст, чтобы геттер не лез повторно в БД
    manager.dialog_data["day_schedule_text"] = format_daily_schedule(daily_schedule)
    await manager.switch_to(ScheduleSG.day_schedule)


# --- Геттеры данных ---


async def get_day_schedule_data(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    return {"schedule_text": dialog_manager.dialog_data["day_schedule_text"]}


async def get_week_schedule_data(
    dialog_manager: DialogManager,
    dbrepositories: DBRepositories,
    **kwargs: Any,
) -> dict[str, Any]:
    group_id = await get_student_group_id(dialog_manager, dbrepositories)
    selected_week = dialog_manager.dialog_data.get("selected_week", "current_week")

    now = datetime.now(TZ_MOSCOW).date()
    helper_day = now if selected_week == "current_week" else now + timedelta(weeks=1)

    weekly_schedule = await get_weekly_schedule(group_id, helper_day, dbrepositories)
    week_stars = "*" if weekly_schedule.week_stars == 1 else "**"

    if selected_week == "current_week":
        text = (
            f"{b(f'📆 Расписание на текущую неделю ({week_stars})')}\n\n{i('🟢 - Текущий день.')}"
        )
    else:
        text = f"{b(f'📆 Расписание на следующую неделю ({week_stars})')}"

    week_days = [
        {
            "date": day.day_date.strftime(DATE_FORMAT),
            "text": class_schedule_onday_b(
                day.day_date,
                current_day=day.is_current_day,
                strikethrough=day.is_non_working_day,
            ).text,
        }
        for day in weekly_schedule.week_days
    ]

    return {"schedule_text": text, "week_days": week_days}


# --- Диалог ---

schedule_dialog = Dialog(
    Window(
        Const(b("🗓️ Расписание")),
        Button(
            Const("📅 Текущая неделя"),
            id="current_week",
            on_click=on_week_schedule,
        ),
        Button(
            Const("📅 Следующая неделя"),
            id="next_week",
            on_click=on_week_schedule,
        ),
        Row(
            Button(
                Const("Сегодня"),
                id="today",
                style=Style(style=ButtonStyle.PRIMARY),
                on_click=on_day_schedule,
            ),
            Button(
                Const("Завтра"),
                id="tomorrow",
                style=Style(style=ButtonStyle.PRIMARY),
                on_click=on_day_schedule,
            ),
        ),
        Cancel(Const("◀️ Назад")),
        state=ScheduleSG.main,
    ),
    Window(
        Format("{schedule_text}"),
        Column(
            Select(
                Format("{item[text]}"),
                id="select_week_day",
                item_id_getter=lambda item: item["date"],
                items="week_days",
                on_click=on_day_schedule,  # Тот же самый обработчик
            )
        ),
        Back(Const("◀️ Назад")),
        state=ScheduleSG.week_schedule,
        getter=get_week_schedule_data,
    ),
    Window(
        Format("{schedule_text}"),
        Button(Const("◀️ Назад"), id="back_from_day", on_click=on_back_from_day),
        state=ScheduleSG.day_schedule,
        getter=get_day_schedule_data,
    ),
)
