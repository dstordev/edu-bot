from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict

from db.models.tables import ReplacementSchedule, Schedule
from db.repositories import DBRepositories
from db.services.working_days import is_non_working_day
from utils.date import get_week_days_from_date
from utils.datetime_format import RU_WEEKDAY_NAMES
from utils.schedule import get_week_stars


# Расписание на день
class DailySchedule(BaseModel):
    weekday_number: int
    day_date: date
    day_name: str
    is_current_day: bool
    classes: list[Schedule | ReplacementSchedule]
    is_non_working_day: bool

    model_config = ConfigDict(arbitrary_types_allowed=True)


# Расписание на неделю
class WeeklySchedule(BaseModel):
    week_number: int
    week_stars: int
    week_days: list[DailySchedule]


async def get_daily_schedule(
    group_id: int, day: date, dbrepositories: DBRepositories
) -> DailySchedule:
    now_day = datetime.now(UTC).astimezone().date()

    schedule = await dbrepositories.replacement_schedule.get_group_lessons_by_day(
        group_id, day
    )
    if len(schedule) == 0:
        schedule = await dbrepositories.schedule.get_group_lessons_by_day(
            group_id,
            day.weekday(),
            len(get_week_stars(day)),
        )

    weekday = day.weekday()
    return DailySchedule(
        weekday_number=weekday,
        day_date=day,
        day_name=RU_WEEKDAY_NAMES[weekday],
        is_current_day=now_day == day,
        classes=list(schedule),
        is_non_working_day=await is_non_working_day(
            group_id=group_id, day=day, dbrepositories=dbrepositories
        ),
    )


async def get_weekly_schedule(
    group_id: int, helper_day: date, dbrepositories: DBRepositories
) -> WeeklySchedule:
    week_days = []
    for day in get_week_days_from_date(helper_day):
        week_days.append(await get_daily_schedule(group_id, day, dbrepositories))

    return WeeklySchedule(
        week_number=helper_day.isocalendar().week,
        week_stars=len(get_week_stars(helper_day)),
        week_days=week_days,
    )
