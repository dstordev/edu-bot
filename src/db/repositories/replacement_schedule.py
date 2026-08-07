from collections.abc import Sequence
from datetime import date, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from db.models.tables import Class, ReplacementSchedule


class ReplacementScheduleRepository:
    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def get_by_day(self, date_: date) -> Sequence[ReplacementSchedule]:
        """Возвращает расписание по дню недели."""

        result = await self.async_session.execute(
            select(ReplacementSchedule).where(ReplacementSchedule.date == date_)
        )
        return result.scalars().all()

    async def get_upcoming_group_lessons(
        self, group_id: int, date_: date, time_: time
    ) -> Sequence[ReplacementSchedule]:
        """Возвращает пары группы, время которых строго больше (после) переданного."""

        result = await self.async_session.execute(
            select(ReplacementSchedule)
            .order_by(Class.start_at.asc())
            .options(
                joinedload(ReplacementSchedule.class_),
                joinedload(ReplacementSchedule.academic_subject),
                joinedload(ReplacementSchedule.audience),
                joinedload(ReplacementSchedule.class_type_),
            )
            .join(Class, ReplacementSchedule.class_id == Class.id)
            .where(
                (ReplacementSchedule.group_id == group_id)
                & (ReplacementSchedule.date == date_)
                & (Class.start_at > time_)
            )
        )
        return result.scalars().all()

    async def get_lessons_by_boundary_time(
        self, date_: date, time_: time
    ) -> Sequence[ReplacementSchedule]:
        """
        Возвращает пары, у которых время начала ИЛИ конца в точности равно target_time.
        Используется для поиска пар на стыке перемен.
        """

        result = await self.async_session.execute(
            select(ReplacementSchedule)
            .options(
                joinedload(ReplacementSchedule.class_),
                joinedload(ReplacementSchedule.academic_subject),
                joinedload(ReplacementSchedule.audience),
                joinedload(ReplacementSchedule.class_type_),
            )
            .join(Class, ReplacementSchedule.class_id == Class.id)
            .where(
                (ReplacementSchedule.date == date_)
                & ((Class.start_at == time_) | (Class.end_at == time_))
            )
        )
        return result.scalars().all()

    async def get_group_lessons_by_day(
        self, group_id: int, date_: date
    ) -> Sequence[ReplacementSchedule]:
        result = await self.async_session.execute(
            select(ReplacementSchedule)
            .options(
                joinedload(ReplacementSchedule.class_),
                joinedload(ReplacementSchedule.academic_subject),
                joinedload(ReplacementSchedule.audience),
                joinedload(ReplacementSchedule.class_type_),
            )
            .join(Class, ReplacementSchedule.class_id == Class.id)
            .where(
                (ReplacementSchedule.group_id == group_id)
                & (ReplacementSchedule.date == date_)
            )
            .order_by(Class.number)
        )
        return result.scalars().all()
