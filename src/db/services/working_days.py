from datetime import date

from db.repositories import DBRepositories
from utils.schedule import get_week_stars


async def is_non_working_day(
    *, group_id: int | None = None, day: date, dbrepositories: DBRepositories
) -> bool:
    """
    Проверяет общие нерабочие дни и отсутствие пар на день у группы.
    Если нигде нет информации, что группа учится в переданный день - возвращается True.
    """

    # Нужно в первую очередь посмотреть на общие нерабочие дни
    result = await dbrepositories.non_working_day.is_non_working_day(day)
    if result is False:
        if group_id is None:
            return False
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
        if len(result) > 0:
            return False

    return True
