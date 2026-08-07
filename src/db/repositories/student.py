from collections.abc import AsyncGenerator

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import Student


class StudentRepository:
    """
    Репозиторий для работы с таблицой студентов в базе данных.
    """

    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def find_by_telegram_id(self, telegram_id: int) -> Student | None:
        result = await self.async_session.execute(
            select(Student).where(Student.telegram_id == telegram_id)
        )
        return result.scalar()

    async def create(
        self, telegram_id: int, name: str, surname: str, patronymic: str, group_id: int
    ) -> int:
        result = await self.async_session.execute(
            insert(Student).returning(Student.id),
            [
                {
                    "telegram_id": telegram_id,
                    "name": name,
                    "surname": surname,
                    "patronymic": patronymic,
                    "group_id": group_id,
                }
            ],
        )
        if (rcontent := result.scalar()) is not None:
            return rcontent
        else:
            raise Exception("Возвращаемое значение не может быть None.")

    async def find(self, student_id: int) -> Student | None:
        result = await self.async_session.execute(
            select(Student).where(Student.id == student_id)
        )
        return result.scalar()

    async def find_students_by_group(self, group_id: int) -> AsyncGenerator[Student]:
        async_result = await self.async_session.stream(
            select(Student).where(Student.group_id == group_id)
        )
        async for row in async_result:
            yield row[0]
