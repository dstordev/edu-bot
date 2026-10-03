from collections.abc import Sequence
from datetime import date, time
from typing import cast

from sqlalchemy import CursorResult, delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from db.models.tables import Class, ReplacementSchedule


class ReplacementScheduleRepository:
    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def add(
        self,
        date_: date,
        group_id: int,
        class_id: int,
        academic_subject_id: int,
        class_type_id: int | None,
        audience_id: int | None,
    ) -> ReplacementSchedule:
        """Добавляет пару к расписанию в базу данных.
        Возвращает добавленный объект."""

        # TODO: добавить проверку на дублирование пары с один день у одной группы с одинаковым class_id.
        result = await self.async_session.execute(
            insert(ReplacementSchedule)
            .values(
                date=date_,
                group_id=group_id,
                class_id=class_id,
                academic_subject_id=academic_subject_id,
                class_type_id=class_type_id,
                audience_id=audience_id,
            )
            .returning(ReplacementSchedule)
        )
        return result.scalar_one()

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

    async def delete_by_group_and_date(self, group_id: int, date_: date) -> bool:
        """Удаляет расписание замен для группы на конкретную дату."""

        r = await self.async_session.execute(
            delete(ReplacementSchedule).where(
                (ReplacementSchedule.group_id == group_id)
                & (ReplacementSchedule.date == date_)
            )
        )
        r = cast(CursorResult, r)
        return r.rowcount > 0
