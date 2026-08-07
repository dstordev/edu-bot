from datetime import date, timedelta


def get_week_days_from_date(date_: date) -> list[date]:
    this_week_day: int = date_.weekday()  # 0 ... 6

    this_week_days: list[date] = []  # текущие дни недели от ПН до ВС

    monday = date_ - timedelta(days=this_week_day)
    for i in range(7):
        this_week_days.append(monday + timedelta(days=i))

    return this_week_days
