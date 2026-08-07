from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import Audience


class AudienceRepository:
    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def get_by_id(self, _id: int) -> Audience | None:
        """
        Возвращает информацию об аудитории по заданному id.
        """

        result = await self.async_session.execute(
            select(Audience).where(Audience.id == _id)
        )
        return result.scalar()
