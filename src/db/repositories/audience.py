from typing import cast

from sqlalchemy import CursorResult, delete, insert, select
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

    async def get_all(self) -> list[Audience]:
        """Возвращает список всех аудиторий."""

        result = await self.async_session.execute(select(Audience))
        return list(result.scalars().all())

    async def add(self, name: str) -> Audience:
        """Добавляет аудиторию в БД и возвращает добавленный объект."""

        r = await self.async_session.execute(
            insert(Audience).values(name=name).returning(Audience)
        )
        return r.scalar_one()

    async def delete_by_id(self, id_: int) -> bool:
        """Удаляет аудиторию из БД по ее id."""

        r = await self.async_session.execute(delete(Audience).where(Audience.id == id_))
        r = cast(CursorResult, r)
        return r.rowcount > 0

    async def find_by_name(self, name: str) -> Audience | None:
        """Ищет и возвращает аудиторию по ее имени."""

        r = await self.async_session.execute(
            select(Audience).where(Audience.name == name)
        )
        return r.scalar_one_or_none()
