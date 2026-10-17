from datetime import date, datetime, timedelta
from typing import Literal

from utils.timezones import TZ_MOSCOW


def get_week_stars(target_date: datetime | date | None = None) -> Literal["*", "**"]:
    """
    Возвращает '*' (числитель) или '**' (знаменатель) для любой переданной даты (по умолчанию — сегодня).

    Работает в любом году без правок кода.
    """

    if isinstance(target_date, datetime):
        target_date = target_date.date()
    elif target_date is None:
        target_date = datetime.now(TZ_MOSCOW).date()

    # 1. Определяем год начала текущего учебного года (без констант)
    acad_year = target_date.year if target_date.month >= 9 else target_date.year - 1
    sept_1 = date(acad_year, 9, 1)

    # 2. Находим понедельник первой учебной недели:
    # Если 1 сентября — воскресенье (weekday == 6), то 1-я неделя начнется с понедельника 2 сентября.
    # В остальных случаях берем понедельник текущей недели.
    if sept_1.weekday() == 6:
        first_monday = sept_1 + timedelta(days=1)
    else:
        first_monday = sept_1 - timedelta(days=sept_1.weekday())

    # 3. Считаем непрерывное количество полных недель от старта года
    # .days // 7 гарантирует, что переход через 31 декабря не собьет счет
    weeks_passed = (target_date - first_monday).days // 7

    # 0, 2, 4... недели -> '*' (1-я неделя)
    # 1, 3, 5... недели -> '**' (2-я неделя)
    return "**" if weeks_passed % 2 else "*"
