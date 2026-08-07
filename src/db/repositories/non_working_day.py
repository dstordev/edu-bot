from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import NonWorkingDay


class NonWorkingDayRepository:
    """
    Репозиторий для работы с таблицой учебных групп в базе данных.
    """

    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def is_non_working_day(self, day: date) -> bool:
        result = await self.async_session.execute(
            select(NonWorkingDay).where(NonWorkingDay.day == day)
        )
        return True if result.scalar() else False

    async def get_non_working_days(self, *, limit: int) -> Sequence[NonWorkingDay]:
        result = await self.async_session.execute(
            select(NonWorkingDay).order_by(NonWorkingDay.day).limit(limit)
        )
        return result.scalars().all()
