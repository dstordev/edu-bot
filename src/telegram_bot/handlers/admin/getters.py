from typing import Any

from db.repositories import DBRepositories


async def get_groups(dbrepositories: DBRepositories, **kwargs: Any) -> dict[str, Any]:
    """Геттер для получения групп."""

    groups = await dbrepositories.group.get_groups()
    return {
        "groups": [{"id": str(group.id), "name": group.name} for group in groups],
    }


async def get_academic_subjects(dbrepositories: DBRepositories, **kwargs: Any) -> dict[str, Any]:
    """Геттер для получения учебных предметов."""

    academic_subjects = await dbrepositories.academic_subject.get_all(limit=40)
    return {
        "academic_subjects": [
            {"id": academic_subject.id, "name": academic_subject.name}
            for academic_subject in academic_subjects
        ]
    }
