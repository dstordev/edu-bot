from datetime import datetime, time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import (
    AcademicSubject,
    Audience,
    Class,
    ClassType,
    Group,
    ReplacementSchedule,
)
from db.repositories import DBRepositories


# Проверка функции get_classes_by_time в из таблицы class.
@pytest.mark.asyncio
async def test_get_classes_by_time(db_session: AsyncSession, test_class: Class):
    """Тест получения занятий по времени начала или конца"""
    dbrepositories = DBRepositories(db_session)

    # Тест поиска по времени начала
    result_start = await dbrepositories.class_.get_classes_by_time(test_class.start_at)
    assert len(result_start) == 1
    assert result_start[0].number == test_class.number
    assert result_start[0].start_at == test_class.start_at
    assert result_start[0].end_at == test_class.end_at

    # Тест поиска по времени конца
    result_end = await dbrepositories.class_.get_classes_by_time(test_class.end_at)
    assert len(result_end) == 1
    assert result_end[0].number == test_class.number

    # Оба результата должны содержать одно и то же занятие
    assert result_start[0].id == result_end[0].id


@pytest.mark.asyncio
async def test_get_classes_by_time_empty_result(db_session: AsyncSession):
    """Тест получения занятий по несуществующему времени"""
    dbrepositories = DBRepositories(db_session)
    result = await dbrepositories.class_.get_classes_by_time(time(23, 59))
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_classes_by_time_multiple_classes(db_session: AsyncSession):
    """Тест получения нескольких занятий с одинаковым временем"""
    class1 = Class(
        number=1,
        start_at=time(8, 30),
        end_at=time(10),
    )
    class2 = Class(
        number=2,
        start_at=time(8, 30),
        end_at=time(11, 30),
    )
    db_session.add_all([class1, class2])
    await db_session.commit()
    dbrepositories = DBRepositories(db_session)
    result = await dbrepositories.class_.get_classes_by_time(time(8, 30))
    assert len(result) == 2
    assert {r.number for r in result} == {1, 2}


@pytest.mark.asyncio
async def test_replacement_schedule_get_by_day_and_stars(
    db_session: AsyncSession,
    test_group: Group,
    test_class: Class,
    test_class_type: ClassType,
    test_academic_subject: AcademicSubject,
    test_audience: Audience,
):
    dbrepositories = DBRepositories(db_session)

    dt = datetime(2000, 2, 5)
    dt2 = datetime(2000, 2, 9)

    replacement_schedule = ReplacementSchedule(
        group_id=test_group.id,
        class_id=test_class.id,
        academic_subject_id=test_academic_subject.id,
        class_type_id=test_class_type.id,
        audience_id=test_audience.id,
        date=dt.date(),
    )
    db_session.add(replacement_schedule)
    replacement_schedule2 = ReplacementSchedule(
        group_id=test_group.id,
        class_id=test_class.id,
        academic_subject_id=test_academic_subject.id,
        class_type_id=test_class_type.id,
        audience_id=test_audience.id,
        date=dt2.date(),
    )
    db_session.add(replacement_schedule2)

    await db_session.commit()

    result = await dbrepositories.replacement_schedule.get_by_day(dt.date())

    assert len(result) == 1

    assert result[0] == replacement_schedule


@pytest.mark.asyncio
async def test_replacement_schedule_get_upcoming_group_lessons(
    db_session: AsyncSession,
    test_group: Group,
    test_class_type: ClassType,
    test_academic_subject: AcademicSubject,
    test_audience: Audience,
):
    dbrepositories = DBRepositories(db_session)

    # Подготавливаем среду
    dt = datetime(2000, 2, 5)

    # Создаем занятия
    class_ = Class(
        number=1,
        start_at=time(8, 30),
        end_at=time(10),
    )
    class_2 = Class(
        number=2,
        start_at=time(10, 10),
        end_at=time(11, 40),
    )
    db_session.add_all([class_, class_2])
    await db_session.commit()

    # Создаем расписание в заменах
    replacement_schedule = ReplacementSchedule(
        id=1,
        group_id=test_group.id,
        class_id=class_.id,
        academic_subject_id=test_academic_subject.id,
        class_type_id=test_class_type.id,
        audience_id=test_audience.id,
        date=dt.date(),
    )
    replacement_schedule_2 = ReplacementSchedule(
        id=2,
        group_id=test_group.id,
        class_id=class_2.id,
        academic_subject_id=test_academic_subject.id,
        class_type_id=test_class_type.id,
        audience_id=test_audience.id,
        date=dt.date(),
    )
    db_session.add_all([replacement_schedule, replacement_schedule_2])
    await db_session.commit()

    # Тестируем функцию
    result = await dbrepositories.replacement_schedule.get_upcoming_group_lessons(
        test_group.id, dt.date(), time(10)
    )

    # Проверяем значения
    assert len(result) == 1
    assert result[0].id == 2
    assert result[0].academic_subject_id == test_academic_subject.id
    assert result[0].academic_subject.name == test_academic_subject.name
    assert result[0].class_.start_at == class_2.start_at


@pytest.mark.asyncio
async def test_local_system_time(db_session: AsyncSession):
    dbrepositories = DBRepositories(db_session)

    class_ = Class(
        number=2,
        start_at=time(10, 10),
        end_at=time(11, 40),
    )
    db_session.add(class_)
    await db_session.commit()
    await db_session.refresh(class_)

    result = await dbrepositories.class_.get_classes_by_time(time(10, 10))

    assert len(result) == 1
    assert result[0].start_at == class_.start_at
    assert result[0].end_at == class_.end_at
    assert result[0].start_at == time(10, 10)
    assert result[0].end_at == time(11, 40)


@pytest.mark.asyncio
async def test_local_system_timeHM(db_session: AsyncSession):
    dbrepositories = DBRepositories(db_session)

    class_ = Class(
        number=2,
        start_at=time(10, 10, 10),
        end_at=time(11, 40),
    )
    db_session.add(class_)
    await db_session.commit()
    await db_session.refresh(class_)

    result = await dbrepositories.class_.get_classes_by_time(time(10, 10, 59))

    assert len(result) == 1
    assert result[0].start_at == class_.start_at
    assert result[0].end_at == class_.end_at
