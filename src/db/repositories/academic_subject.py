from collections.abc import Sequence

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import AcademicSubject


class AcademicSubjectRepository:
    """
    Репозиторий для работы с таблицой предметов в базе данных.
    """

    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def get_by_id(self, academic_subject_id: int) -> AcademicSubject | None:
        result = await self.async_session.execute(
            select(AcademicSubject).where(AcademicSubject.id == academic_subject_id)
        )
        return result.scalar()

    async def get_all(
        self, *, limit: int = 10, page_index: int = 0
    ) -> Sequence[AcademicSubject]:
        result = await self.async_session.execute(
            select(AcademicSubject)
            .order_by(AcademicSubject.name.asc())
            .limit(limit)
            .offset(page_index * limit)
        )
        return result.scalars().all()

    async def add(self, name: str) -> AcademicSubject:
        """Добавляет новый учебный предмет в базу данных.
        Возвращает добавленный объект."""

        result = await self.async_session.execute(
            insert(AcademicSubject).values(name=name).returning(AcademicSubject)
        )
        return result.scalar_one()

    async def find_by_name(self, name: str) -> AcademicSubject | None:
        """Ищет и возвращает учебный предмет по его имени."""

        r = await self.async_session.execute(
            select(AcademicSubject).where(AcademicSubject.name == name)
        )
        return r.scalar_one_or_none()
