from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import (
    AcademicSubject,
    Audience,
    Class,
    ClassType,
    Group,
    NonWorkingDay,
    ReplacementSchedule,
    Schedule,
)
from db.repositories import DBRepositories
from utils.schedule import get_week_stars


@pytest.mark.asyncio
async def test_is_non_working_day(db_session: AsyncSession):
    dbrepositories = DBRepositories(db_session)

    day = datetime.now(UTC).date()

    non_working_day = NonWorkingDay(day=day)
    db_session.add(non_working_day)
    await db_session.flush()

    assert non_working_day.id is not None

    result = await dbrepositories.non_working_day.is_non_working_day(
        non_working_day.day
    )

    assert result is True


@pytest.mark.asyncio
async def test_get_group_lessons_by_day_replacement_schedule(
    db_session: AsyncSession,
    test_group: Group,
    test_class: Class,
    test_academic_subject: AcademicSubject,
    test_class_type: ClassType,
    test_audience: Audience,
):
    dbrepositories = DBRepositories(db_session)

    date_ = datetime(2026, 1, 9).date()
    group_id = test_group.id

    replacement_schedule = ReplacementSchedule(
        group_id=group_id,
        class_id=test_class.id,
        academic_subject_id=test_academic_subject.id,
        class_type_id=test_class_type.id,
        audience_id=test_audience.id,
        date=date_,
    )
    db_session.add(replacement_schedule)
    await db_session.flush()

    result = await dbrepositories.replacement_schedule.get_group_lessons_by_day(
        group_id, date_
    )

    assert len(result) == 1
    assert replacement_schedule.date == date_


@pytest.mark.asyncio
async def test_get_group_lessons_by_day_schedule(
    db_session: AsyncSession,
    test_group: Group,
    test_class: Class,
    test_academic_subject: AcademicSubject,
    test_class_type: ClassType,
    test_audience: Audience,
):
    dbrepositories = DBRepositories(db_session)

    dt = datetime(2026, 1, 9)
    dt_day = dt.weekday()
    dt_stars = len(get_week_stars(dt))
    group_id = test_group.id

    schedule = Schedule(
        group_id=group_id,
        class_id=test_class.id,
        academic_subject_id=test_academic_subject.id,
        class_type_id=test_class_type.id,
        audience_id=test_audience.id,
        week_day=dt_day,
        stars=dt_stars,
    )
    db_session.add(schedule)
    await db_session.flush()

    result = await dbrepositories.schedule.get_group_lessons_by_day(
        group_id, dt_day, dt_stars
    )

    assert len(result) == 1
    assert schedule.week_day == dt_day
    assert schedule.stars == dt_stars
