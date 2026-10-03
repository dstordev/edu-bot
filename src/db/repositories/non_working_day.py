from collections.abc import Sequence
from datetime import date
from typing import cast

from sqlalchemy import CursorResult, delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import NonWorkingDay


class NonWorkingDayRepository:
    """
    Репозиторий для работы с таблицой учебных групп в базе данных.
    """

    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def is_non_working_day(self, day: date, group_id: int | None = None) -> bool:
        """
        group_id - Если в значение передан `None`, то функция вернет общие нерабочие дни, для которых не указана группа,
        а если id группы указан, то функция вернет нерабочие дни для конкретной группы.
        """
        result = await self.async_session.execute(
            select(NonWorkingDay).where(
                (NonWorkingDay.day == day) & (NonWorkingDay.group_id == group_id)
            )
        )
        return bool(result.scalar())

    async def get_non_working_days(self, *, limit: int) -> Sequence[NonWorkingDay]:
        result = await self.async_session.execute(
            select(NonWorkingDay).order_by(NonWorkingDay.day).limit(limit)
        )
        return result.scalars().all()

    async def add(self, day: date, group_id: int | None) -> NonWorkingDay:
        """
        Добавляет нерабочий день.
        Если в group_id передан None, то нерабочий день считается как общий.
        """
        r = await self.async_session.execute(
            insert(NonWorkingDay)
            .values(day=day, group_id=group_id)
            .returning(NonWorkingDay)
        )
        return r.scalar_one()

    async def delete(self, day: date, group_id: int | None) -> bool:
        """
        Удаляет нерабочий день.
        Если в group_id передан None, то нерабочий день считается как общий.
        """
        r = await self.async_session.execute(
            delete(NonWorkingDay).where(
                (NonWorkingDay.day == day) & (NonWorkingDay.group_id == group_id)
            )
        )
        r = cast(CursorResult, r)
        return r.rowcount > 0
