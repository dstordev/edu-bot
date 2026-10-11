from sqlalchemy.ext.asyncio import AsyncSession

from .academic_subject import AcademicSubjectRepository
from .audience import AudienceRepository
from .class_ import ClassRepository
from .class_type import ClassTypeRepository
from .group import GroupRepository
from .homework import HomeworkRepository
from .non_working_day import NonWorkingDayRepository
from .replacement_schedule import ReplacementScheduleRepository
from .schedule import ScheduleRepository
from .student import StudentRepository
from .student_homework import StudentHomeworkRepository
from .student_settings import StudentSettingsRepository


class DBRepositories:
    def __init__(self, async_session: AsyncSession) -> None:
        self.academic_subject = AcademicSubjectRepository(async_session)
        self.group = GroupRepository(async_session)
        self.student = StudentRepository(async_session)
        self.class_ = ClassRepository(async_session)
        self.schedule = ScheduleRepository(async_session)
        self.replacement_schedule = ReplacementScheduleRepository(async_session)
        self.audience = AudienceRepository(async_session)
        self.non_working_day = NonWorkingDayRepository(async_session)
        self.student_homework = StudentHomeworkRepository(async_session)
        self.homework = HomeworkRepository(async_session)
        self.class_type = ClassTypeRepository(async_session)
        self.student_settings = StudentSettingsRepository(async_session)
