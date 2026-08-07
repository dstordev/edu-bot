from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import StudentHomework


class StudentHomeworkRepository:
    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def mark_completed(self, *, student_id: int, homework_id: int) -> int:
        result = await self.async_session.execute(
            insert(StudentHomework)
            .values(student_id=student_id, homework_id=homework_id)
            .returning(StudentHomework.id)
        )
        shid = result.scalar()
        assert shid is not None

        return shid
