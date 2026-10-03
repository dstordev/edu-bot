from datetime import datetime

import pytest

from utils.schedule import get_week_stars
from utils.timezones import TZ_MOSCOW


@pytest.mark.parametrize(
    "test_date,expected_stars",
    [
        # Нечетные недели (возвращают "*")
        (datetime(2000, 2, 5, tzinfo=TZ_MOSCOW), "*"),  # Суббота, нечетная неделя
        (datetime(2000, 2, 6, tzinfo=TZ_MOSCOW), "*"),  # Воскресенье, нечетная неделя
        (datetime(2000, 1, 3, tzinfo=TZ_MOSCOW), "*"),  # Понедельник, нечетная неделя
        # Четные недели (возвращают "**")
        (datetime(2000, 2, 7, tzinfo=TZ_MOSCOW), "**"),  # Понедельник, четная неделя
        (datetime(2000, 2, 13, tzinfo=TZ_MOSCOW), "**"),  # Воскресенье, четная неделя
        (datetime(2000, 1, 10, tzinfo=TZ_MOSCOW), "**"),  # Понедельник, четная неделя
    ],
)
def test_get_week_stars(test_date: datetime, expected_stars: str):
    """Тест функции определения типа недели (звездочки)"""
    assert get_week_stars(test_date) == expected_stars
