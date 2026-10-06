from db.repositories._repositories import DBRepositories


async def get_groups(dbrepositories: DBRepositories, **kwargs):
    """Геттер для получения групп."""

    groups = await dbrepositories.group.get_groups()
    return {
        "groups": [{"id": str(group.id), "name": group.name} for group in groups],
    }


async def get_academic_subjects(dbrepositories: DBRepositories, **kwargs):
    """Геттер для получения учебных предметов."""

    academic_subjects = await dbrepositories.academic_subject.get_all(limit=20)
    return {
        "academic_subjects": [
            {"id": academic_subject.id, "name": academic_subject.name}
            for academic_subject in academic_subjects
        ]
    }
