from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import StudentSettings


class StudentSettingsRepository:
    def __init__(self, async_session: AsyncSession) -> None:
        self.async_session = async_session

    async def add(self, student_id: int) -> StudentSettings:
        r = await self.async_session.execute(
            insert(StudentSettings)
            .values(student_id=student_id)
            .returning(StudentSettings)
        )
        return r.scalar_one()

    async def find(self, student_id: int) -> StudentSettings | None:
        r = await self.async_session.execute(
            select(StudentSettings).where(StudentSettings.student_id == student_id)
        )
        return r.scalar_one_or_none()

    async def set_reminder_5min(self, student_id: int, enabled: bool) -> None:
        await self.async_session.execute(
            update(StudentSettings)
            .where(StudentSettings.student_id == student_id)
            .values(reminder_5min=enabled)
        )
