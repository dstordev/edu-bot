from collections.abc import Sequence
from datetime import date

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from db.models.tables import Homework, HomeworkFile, HomeworkPhoto, StudentHomework


class HomeworkRepository:
    def __init__(self, async_session: AsyncSession) -> None:
        self.async_session = async_session

    async def add_homework(
        self,
        *,
        academic_subject_id: int,
        text: str,
        assignment_date: date | None = None,
        photo_telegram_file_ids: list[str] | None = None,
        file_telegram_file_ids: list[str] | None = None,
    ) -> int:
        result = await self.async_session.execute(
            insert(Homework)
            .values(
                academic_subject_id=academic_subject_id,
                text=text,
                assignment_date=assignment_date,
            )
            .returning(Homework.id)
        )

        homework_id = result.scalar()
        assert homework_id is not None

        if photo_telegram_file_ids is not None:
            for photo_telegram_file_id in photo_telegram_file_ids:
                await self.async_session.execute(
                    insert(HomeworkPhoto).values(
                        homework_id=homework_id, telegram_file_id=photo_telegram_file_id
                    )
                )

        if file_telegram_file_ids is not None:
            for file_telegram_file_id in file_telegram_file_ids:
                await self.async_session.execute(
                    insert(HomeworkFile).values(
                        homework_id=homework_id, telegram_file_id=file_telegram_file_id
                    )
                )

        return homework_id

    async def get_unfinished_homeworks(
        self,
        student_id: int,
        limit: int = 10,
        page_index: int = 0,
    ) -> Sequence[Homework]:
        result = await self.async_session.execute(
            select(Homework)
            .options(
                joinedload(Homework.student_homework),
                joinedload(Homework.homework_photo),
                joinedload(Homework.homework_file),
                joinedload(Homework.academic_subject),
            )
            .where(
                ~(
                    select(StudentHomework.id).where(
                        (StudentHomework.student_id == student_id)
                        & (StudentHomework.homework_id == Homework.id)
                    )
                ).exists()
            )
            .order_by(Homework.id.desc())
            .limit(limit)
            .offset(page_index * limit)
        )
        return result.unique().scalars().all()

    async def get_finished_homeworks(
        self,
        student_id: int,
        limit: int = 10,
        page_index: int = 0,
    ) -> Sequence[Homework]:
        result = await self.async_session.execute(
            select(Homework)
            .options(
                joinedload(Homework.student_homework),
                joinedload(Homework.homework_photo),
                joinedload(Homework.homework_file),
                joinedload(Homework.academic_subject),
            )
            .where(
                (
                    select(StudentHomework.id).where(
                        (StudentHomework.student_id == student_id)
                        & (StudentHomework.homework_id == Homework.id)
                    )
                ).exists()
            )
            .order_by(Homework.id.desc())
            .limit(limit)
            .offset(page_index * limit)
        )
        return result.unique().scalars().all()

    async def get_homework(self, homework_id: int) -> Homework | None:
        result = await self.async_session.execute(
            select(Homework)
            .options(
                joinedload(Homework.homework_photo),
                joinedload(Homework.homework_file),
                joinedload(Homework.academic_subject),
            )
            .where(Homework.id == homework_id)
        )
        return result.scalar()

    async def is_finished_homework(self, *, homework_id: int, student_id: int) -> bool:
        result = await self.async_session.execute(
            select(StudentHomework.id).where(
                (StudentHomework.homework_id == homework_id)
                & (StudentHomework.student_id == student_id)
            )
        )
        return result.scalar() is not None
