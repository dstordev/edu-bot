from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import Group


class GroupRepository:
    """
    Репозиторий для работы с таблицой учебных групп в базе данных.
    """

    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def get_groups(self) -> list[Group]:
        result = await self.async_session.execute(select(Group))
        return list(result.scalars().all())

    async def find_by_name(self, name: str) -> Group | None:
        result = await self.async_session.execute(
            select(Group).where(Group.name == name)
        )
        return result.scalar()

    async def create(self):
        pass
