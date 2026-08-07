from collections.abc import Sequence
from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import Class


class ClassRepository:
    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    # Получение занятий
    async def get_classes(self) -> Sequence[Class]:
        result = await self.async_session.execute(select(Class))
        return result.scalars().all()

    # Возвращает пары, у которых время начала или время конца совпадает с переданным временем
    async def get_classes_by_time(self, iso_time: time) -> Sequence[Class]:
        result = await self.async_session.execute(
            select(Class).where(
                (Class.start_at == iso_time) | (Class.end_at == iso_time)
            )
        )
        return result.scalars().all()
