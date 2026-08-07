from datetime import UTC, datetime, time

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from db.models.base import Base
from db.models.tables import (
    AcademicSubject,
    Audience,
    Class,
    ClassType,
    Group,
    Student,
)
from settings import settings

TEST_DATABASE_URL = settings.TEST_POSTGRES_URL


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Создаем таблицы перед тестами
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine: AsyncEngine):
    connection = await db_engine.connect()
    trans = await connection.begin()

    async_session = AsyncSession(bind=connection, expire_on_commit=False)

    yield async_session

    await async_session.close()
    await trans.rollback()
    await connection.close()


# Фикстуры для создания тестовых данных
@pytest_asyncio.fixture
async def test_group(db_session: AsyncSession) -> Group:
    """Создает тестовую группу"""
    group = Group(name="TEST-01")
    db_session.add(group)
    await db_session.flush()
    await db_session.refresh(group)
    return group


@pytest_asyncio.fixture
async def test_academic_subject(db_session: AsyncSession) -> AcademicSubject:
    """Создает тестовый учебный предмет"""
    subject = AcademicSubject(name="Математика")
    db_session.add(subject)
    await db_session.flush()
    await db_session.refresh(subject)
    return subject


@pytest_asyncio.fixture
async def test_audience(db_session: AsyncSession) -> Audience:
    """Создает тестовую аудиторию"""
    audience = Audience(name="101")
    db_session.add(audience)
    await db_session.flush()
    await db_session.refresh(audience)
    return audience


@pytest_asyncio.fixture
async def test_class_type(db_session: AsyncSession) -> ClassType:
    """Создает тестовый тип занятия"""
    class_type = ClassType(name="Лекция")
    db_session.add(class_type)
    await db_session.flush()
    await db_session.refresh(class_type)
    return class_type


@pytest_asyncio.fixture
async def test_class(db_session: AsyncSession) -> Class:
    """Создает тестовое занятие"""
    local_tzinfo = datetime.now(UTC).astimezone().tzinfo

    class_ = Class(
        number=1,
        start_at=time(8, 30, tzinfo=local_tzinfo),
        end_at=time(10, tzinfo=local_tzinfo),
    )
    db_session.add(class_)
    await db_session.flush()
    await db_session.refresh(class_)
    return class_


@pytest_asyncio.fixture
async def test_student(db_session: AsyncSession, test_group: Group) -> Student:
    """Создает тестового студента"""
    student = Student(
        telegram_id=123456789,
        name="Иван",
        surname="Иванов",
        patronymic="Иванович",
        group_id=test_group.id,
    )
    db_session.add(student)
    await db_session.flush()
    await db_session.refresh(student)
    return student
