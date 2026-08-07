from collections.abc import Sequence
from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from db.models.tables import Class, Schedule


class ScheduleRepository:
    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def get_lessons_by_boundary_time(
        self, week_day: date, week_stars: int, target_time: time
    ) -> Sequence[Schedule]:
        """
        Возвращает пары, у которых время начала ИЛИ конца в точности равно target_time.
        Используется для поиска пар на стыке перемен.
        """

        result = await self.async_session.execute(
            select(Schedule)
            .options(
                joinedload(Schedule.class_),
                joinedload(Schedule.academic_subject),
                joinedload(Schedule.audience),
                joinedload(Schedule.class_type_),
            )
            .join(Class, Schedule.class_id == Class.id)
            .where(
                (Schedule.week_day == week_day.weekday())
                & (Schedule.stars == week_stars)
                & ((Class.start_at == target_time) | (Class.end_at == target_time))
            )
        )
        return result.scalars().all()

    async def get_upcoming_group_lessons(
        self, group_id: int, week_day: date, week_stars: int, time_: time
    ) -> Sequence[Schedule]:
        """Возвращает пары группы, время которых строго больше (после) переданного."""

        result = await self.async_session.execute(
            select(Schedule)
            .order_by(Class.start_at.asc())
            .options(
                joinedload(Schedule.class_),
                joinedload(Schedule.academic_subject),
                joinedload(Schedule.audience),
                joinedload(Schedule.class_type_),
            )
            .join(Class, Schedule.class_id == Class.id)
            .where(
                (Schedule.group_id == group_id)
                & (Schedule.week_day == week_day.weekday())
                & (Schedule.stars == week_stars)
                & (Class.start_at > time_)
            )
        )
        return result.scalars().all()

    async def get_group_lessons_by_day(
        self, group_id: int, week_day: int, week_stars: int
    ) -> Sequence[Schedule]:
        result = await self.async_session.execute(
            select(Schedule)
            .options(
                joinedload(Schedule.class_),
                joinedload(Schedule.academic_subject),
                joinedload(Schedule.audience),
                joinedload(Schedule.class_type_),
            )
            .join(Class, Schedule.class_id == Class.id)
            .where(
                (Schedule.group_id == group_id)
                & (Schedule.week_day == week_day)
                & (Schedule.stars == week_stars)
            )
            .order_by(Class.number)
        )
        return result.scalars().all()
