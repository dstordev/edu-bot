from collections.abc import Sequence

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import SurveyData
from enums import SurveyState


class SurveyDataRepository:
    """
    Репозиторий для работы с таблицой данных опросов базе данных.
    """

    def __init__(self, async_session: AsyncSession):
        self.async_session = async_session

    async def tag_student_in_survey(
        self, survey_id: int, student_id: int, state: SurveyState
    ) -> int:
        result = await self.async_session.execute(
            insert(SurveyData).returning(SurveyData.id),
            [{"survey_id": survey_id, "student_id": student_id, "state": state}],
        )
        if (rcontent := result.scalar()) is not None:
            return rcontent
        else:
            raise Exception("Возвращаемое значение не может быть None.")

    async def find_students_tags_in_survey(
        self, survey_id: int
    ) -> Sequence[SurveyData]:
        result = await self.async_session.execute(
            select(SurveyData).where(SurveyData.survey_id == survey_id)
        )
        return result.scalars().all()
