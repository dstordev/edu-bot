from aiogram import Bot
from aiogram.exceptions import AiogramError, TelegramForbiddenError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.repositories._repositories import DBRepositories


async def notify_students_by_group(
    group_id: int,
    text: str,
    async_sessmaker: async_sessionmaker[AsyncSession],
    bot: Bot,
) -> tuple[int, int]:
    """
    Рассылает студентам указанной группе указаный текст.
    Возввращает кортеж (кол-во студентов, кол-во неудачных отправок).
    """

    async with async_sessmaker.begin() as session:
        repos = DBRepositories(session)
        return await notify_students_by_group_repos(group_id, text, repos, bot)


async def notify_students_by_group_repos(
    group_id: int,
    text: str,
    dbrepositories: DBRepositories,
    bot: Bot,
) -> tuple[int, int]:
    """
    (Версия с передачей готовой dbrepositories)

    Рассылает студентам указанной группе указаный текст.
    Возввращает кортеж (кол-во студентов, кол-во неудачных отправок).
    """

    count_error = 0
    count = 0
    async for student in dbrepositories.student.find_students_by_group(group_id):
        count += 1

        has_err = False

        if student.is_active:
            try:
                await bot.send_message(chat_id=student.telegram_id, text=text)
            except TelegramForbiddenError:
                has_err = True
                logger.warning(
                    "[Notify] Не удалось отправить студенту сообщение из-за того, что пользователь заблокировал бота."
                )

                # Пытаемся пометить студента как неактивного
                try:
                    await dbrepositories.student.mark_activity(
                        student.id, is_active=False
                    )
                except Exception as ex:
                    logger.error(f"Не удалось пометить активность студента: {ex}")
            except AiogramError as ex:
                has_err = True
                logger.error(
                    f"[Notify] При отправке сообщения студенту произошла ошибка: {ex}"
                )
        else:
            has_err = True

        if has_err:
            count_error += 1

    return count, count_error
