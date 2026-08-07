from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tables import AcademicSubject, Student
from db.repositories import DBRepositories


@pytest.mark.asyncio
async def test_homeworks_flow(
    db_session: AsyncSession,
    test_student: Student,
    test_academic_subject: AcademicSubject,
):
    dbrepositories = DBRepositories(db_session)

    # Создаем домашние задания
    files = ["file1", "file2"]
    homework_id1 = await dbrepositories.homework.add_homework(
        academic_subject_id=test_academic_subject.id,
        text="Нужно сделать несколько упражнений с 100 по 102.",
        assignment_date=date(year=2026, month=1, day=20),
        photo_telegram_file_ids=files,
        file_telegram_file_ids=files,
    )
    assert homework_id1 == 1

    homework_id2 = await dbrepositories.homework.add_homework(
        academic_subject_id=test_academic_subject.id,
        text="Нужно сделать несколько упражнений с 50 по 53.",
        assignment_date=date(year=2026, month=1, day=15),
    )
    assert homework_id2 == 2

    homework_id3 = await dbrepositories.homework.add_homework(
        academic_subject_id=test_academic_subject.id,
        text="Нужно сделать несколько упражнений с 30 по 33.",
        assignment_date=date(year=2026, month=1, day=10),
    )
    assert homework_id3 == 3

    # Отмечаем одно задание как выполненное
    result = await dbrepositories.student_homework.mark_completed(
        student_id=test_student.id, homework_id=homework_id2
    )

    # Получаем невыполненные задания
    result = await dbrepositories.homework.get_unfinished_homeworks(test_student.id)

    assert len(result) == 2
    assert result[1].academic_subject_id == test_academic_subject.id
    assert result[1].id == homework_id1
    assert result[1].homework_file[0].telegram_file_id == files[0]

    # Получаем выполненные задания

    result = await dbrepositories.homework.get_finished_homeworks(test_student.id)

    assert len(result) == 1
    assert result[0].id == homework_id2
