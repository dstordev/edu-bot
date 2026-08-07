from collections.abc import Sequence

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import Survey


class SurveyRepository:
    """
    Репозиторий для работы с таблицой опросов в базе данных.
    """

    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def create(self) -> Survey:
        result = await self.async_session.execute(insert(Survey).returning(Survey))
        if (rcontent := result.scalar()) is not None:
            return rcontent
        else:
            raise Exception("Возвращаемое значение не может быть None.")

    async def get_surveys(self, limit: int = 10) -> Sequence[Survey]:
        result = await self.async_session.execute(
            select(Survey).order_by(Survey.id.desc()).limit(limit)
        )
        return result.scalars().all()
