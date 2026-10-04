from datetime import date

from db.repositories import DBRepositories
from utils.schedule import get_week_stars


async def is_non_working_day(
    *, day: date, dbrepositories: DBRepositories, group_id: int | None = None
) -> bool:
    """
    Проверяет не рабочий ли сегодня день.
    """

    if await dbrepositories.non_working_day.is_non_working_day(day):
        return True
    return bool(
        group_id
        and await dbrepositories.non_working_day.is_non_working_day(day, group_id)
    )


async def is_non_working_day_and_no_schedule(
    *, group_id: int | None = None, day: date, dbrepositories: DBRepositories
) -> bool:
    """
    Проверяет общие нерабочие дни и отсутствие пар на день у группы.
    Если нигде нет информации, что группа учится в переданный день - возвращается True.
    """

    if await is_non_working_day(
        day=day, group_id=group_id, dbrepositories=dbrepositories
    ):
        return True

    if group_id:
        # Ещё проверяем расписание у этой группы
        # Проверяем в расписании замен
        result = await dbrepositories.replacement_schedule.get_group_lessons_by_day(
            group_id, day
        )
        if len(result) > 0:
            return False

        # Проверяем в статическом расписании
        result = await dbrepositories.schedule.get_group_lessons_by_day(
            group_id, day.weekday(), len(get_week_stars(day))
        )
        return not len(result) > 0
    else:
        return False
