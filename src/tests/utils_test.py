from datetime import datetime

import pytest

from utils.schedule import get_week_stars


@pytest.mark.parametrize(
    "test_date,expected_stars",
    [
        # Нечетные недели (возвращают "*")
        (datetime(2000, 2, 5), "*"),  # Суббота, нечетная неделя
        (datetime(2000, 2, 6), "*"),  # Воскресенье, нечетная неделя
        (datetime(2000, 1, 3), "*"),  # Понедельник, нечетная неделя
        # Четные недели (возвращают "**")
        (datetime(2000, 2, 7), "**"),  # Понедельник, четная неделя
        (datetime(2000, 2, 13), "**"),  # Воскресенье, четная неделя
        (datetime(2000, 1, 10), "**"),  # Понедельник, четная неделя
    ],
)
def test_get_week_stars(test_date: datetime, expected_stars: str):
    """Тест функции определения типа недели (звездочки)"""
    assert get_week_stars(test_date) == expected_stars
