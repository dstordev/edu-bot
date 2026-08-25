from datetime import date as dt_date
from datetime import datetime, time
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    Time,
    TypeDecorator,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from db.models.base import Base


class TIME_HM(TypeDecorator):
    impl = Time
    cache_ok = True

    def process_bind_param(self, value: time | Any, dialect) -> time | None:
        """Перед записью в БД: переводим всё в UTC"""

        return value.replace(second=0, microsecond=0)

    def process_result_value(self, value: time | Any, dialect) -> time | None:
        """После чтения из БД: переводим в локальное время ОС"""

        return value.replace(second=0, microsecond=0)


class Student(Base):
    """Модель студента.

    Хранит персональные данные студента, его Telegram ID,
    связь с учебной группой и метки времени создания/обновления записи.

    Attributes:
        id (int): Уникальный идентификатор записи (Primary Key).
        telegram_id (int): Идентификатор пользователя в Telegram (BigInteger, Unique).
        name (str): Имя студента (до 30 символов).
        surname (str): Фамилия студента (до 30 символов).
        patronymic (str | None): Отчество студента (опционально, до 30 символов).
        group_id (int): Внешний ключ, указывающий на группу студента (FK -> group.id).
        created_at (datetime): Дата и время создания записи (автоматически при вставке).
        updated_at (datetime): Дата и время последнего обновления (автоматически при изм.).
    """

    __tablename__ = "student"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String(30))
    surname: Mapped[str] = mapped_column(String(30))
    patronymic: Mapped[str | None] = mapped_column(String(30))
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
    )


class Survey(Base):
    """Модель опроса.

    Хранит идентификатор опроса и метку времени создания записи.

    Attributes:
        id (int): Уникальный идентификатор записи (Primary Key).
        created_at (datetime): Дата и время создания записи (автоматически при вставке).
    """

    __tablename__ = "survey"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SurveyData(Base):
    """Модель данных прохождения опроса.

    Хранит информацию о прохождении опроса конкретным студентом,
    текущее состояние опроса и метки времени создания/обновления записи.

    Attributes:
        id (int): Уникальный идентификатор записи (Primary Key).
        survey_id (int): Внешний ключ, указывающий на опрос (FK -> survey.id).
        student_id (int): Внешний ключ, указывающий на студента (FK -> student.id).
        state (int): Числовой статус или состояние прохождения опроса.
        created_at (datetime): Дата и время создания записи (автоматически при вставке).
        updated_at (datetime): Дата и время последнего обновления (автоматически при изм.).
    """

    __tablename__ = "survey_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    survey_id: Mapped[int] = mapped_column(ForeignKey("survey.id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))
    state: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
    )


class Group(Base):
    __tablename__ = "group"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(15), unique=True)
    token: Mapped[str] = mapped_column(
        String(5), unique=True, server_default=text("generate_group_token()")
    )
    created_at: Mapped[datetime] = (
        mapped_column(  # TODO: удалить колонку, так как нет смысла знать эту информацию
            DateTime(timezone=True), server_default=func.now()
        )
    )


class AcademicSubject(Base):
    __tablename__ = "academic_subject"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    created_at: Mapped[datetime] = (
        mapped_column(  # TODO: удалить колонку, так как нет смысла знать эту информацию
            DateTime(timezone=True), server_default=func.now()
        )
    )


# Storage for classes/lessons
class Class(Base):
    __tablename__ = "class"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int]
    start_at: Mapped[time] = mapped_column(
        TIME_HM
    )  # time in iso 8601 format up to minutes
    end_at: Mapped[time] = mapped_column(
        TIME_HM
    )  # time in iso 8601 format up to minutes


class _ScheduleMixin:
    """Общие колонки для сущностей расписания"""

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"))
    class_id: Mapped[int] = mapped_column(ForeignKey("class.id"))
    academic_subject_id: Mapped[int] = mapped_column(ForeignKey("academic_subject.id"))
    class_type_id: Mapped[int] = mapped_column(ForeignKey("class_type.id"))
    audience_id: Mapped[int] = mapped_column(ForeignKey("audience.id"))

    @declared_attr
    def academic_subject(cls):
        return relationship("AcademicSubject")

    @declared_attr
    def audience(cls):
        return relationship("Audience")

    @declared_attr
    def class_(cls):
        return relationship("Class")

    @declared_attr
    def class_type_(cls):
        return relationship("ClassType")


class Schedule(_ScheduleMixin, Base):
    """Постоянное (недельное) расписание занятий группы — запись описывает одну пару."""

    __tablename__ = "schedule"

    stars: Mapped[int]  # 1 or 2.
    week_day: Mapped[int]  # Monday == 0 ... Sunday == 6.


class ReplacementSchedule(_ScheduleMixin, Base):
    """Расписание замен: замена на конкретную дату (YYYY-MM-DD)."""

    __tablename__ = "replacement_schedule"

    date: Mapped[dt_date]  # ISO format YYYY-MM-DD


class ClassType(Base):
    __tablename__ = "class_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)


class Audience(Base):
    __tablename__ = "audience"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)


class NonWorkingDay(Base):
    """Дни, в которые студенты не учатся."""

    __tablename__ = "non_working_day"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[dt_date] = mapped_column(unique=True)


class Homework(Base):
    __tablename__ = "homework"

    id: Mapped[int] = mapped_column(primary_key=True)
    academic_subject_id: Mapped[int] = mapped_column(ForeignKey("academic_subject.id"))
    text: Mapped[str]
    assignment_date: Mapped[dt_date | None]

    student_homework = relationship("StudentHomework")
    homework_photo = relationship("HomeworkPhoto")
    homework_file = relationship("HomeworkFile")
    academic_subject = relationship("AcademicSubject")


class StudentHomework(Base):
    __tablename__ = "student_homework"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))
    homework_id: Mapped[int] = mapped_column(ForeignKey("homework.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "homework_id",
            name="student_homework_student_id_homework_id_key",
        ),
    )


class _HomeworkFileMixin:
    id: Mapped[int] = mapped_column(primary_key=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey("homework.id"))
    telegram_file_id: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class HomeworkPhoto(_HomeworkFileMixin, Base):
    __tablename__ = "homework_photo"

    __table_args__ = (
        UniqueConstraint(
            "homework_id",
            "telegram_file_id",
            name="homework_photo_homework_id_telegram_file_id_key",
        ),
    )


class HomeworkFile(_HomeworkFileMixin, Base):
    __tablename__ = "homework_file"

    __table_args__ = (
        UniqueConstraint(
            "homework_id",
            "telegram_file_id",
            name="homework_file_homework_id_telegram_file_id_key",
        ),
    )
