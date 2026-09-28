from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import ClassType


class ClassTypeRepository:
    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def get_all(self) -> list[ClassType]:
        """Возвращает список всех типов пар."""

        result = await self.async_session.execute(select(ClassType))
        return list(result.scalars().all())
