from datetime import date, datetime
from typing import Literal


def get_week_stars(_dt: datetime | date) -> Literal["*", "**"]:
    return "**" if _dt.isocalendar().week % 2 == 0 else "*"
