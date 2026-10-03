from collections.abc import Generator
from datetime import date, datetime, time, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.models.tables import ReplacementSchedule, Schedule
from db.repositories import DBRepositories
from db.services.working_days import is_non_working_day
from telegram_bot.windows.registered import (
    InfoWindow,
    notification_end_at_window,
    notification_start_at_window,
)
from utils.notify_students import notify_students_by_group_repos
from utils.schedule import get_week_stars
from utils.timezones import TZ_MOSCOW

ScheduleItem = ReplacementSchedule | Schedule


class ScheduleNotifier:
    """Контролирует рассылку уведомлений студентам о начале и конце пар."""

    def __init__(
        self, bot: Bot, async_sessionmaker: async_sessionmaker[AsyncSession]
    ) -> None:
        self.__bot = bot
        self.__async_sessionmaker = async_sessionmaker
        self.__scheduler = AsyncIOScheduler()

    def run_monitor(self) -> None:
        """Запускает фоновый планировщик проверки расписания каждую минуту."""

        self.__scheduler.add_job(
            self.check_class_and_notify,
            "interval",
            minutes=1,
            max_instances=1,
            coalesce=True,
        )
        self.__scheduler.start()

    async def check_class_and_notify(self) -> None:
        """Проверяет пары через 5 минут и рассылает уведомления студентам."""

        target_dt = (datetime.now(TZ_MOSCOW) + timedelta(minutes=5)).replace(
            second=0, microsecond=0
        )
        target_date, target_time = target_dt.date(), target_dt.time()

        async with self.__async_sessionmaker() as session:
            repos = DBRepositories(session)

            if await is_non_working_day(day=target_date, dbrepositories=repos):
                return

            replacement_groups = await self.find_group_ids_in_replacement_schedules(
                target_date, repos
            )

            schedules: list[tuple[ScheduleItem, ScheduleItem | None]] = []
            schedules.extend(
                await self.find_schedules(
                    target_date, target_time, replacement_groups, repos
                )
            )

            if replacement_groups:
                schedules.extend(
                    await self.find_replacement_schedules(
                        target_date, target_time, repos
                    )
                )

            if not schedules:
                return

            for group_id, window in self.prepare_student_data_notification(
                schedules, repos, target_time
            ):
                logger.debug(f"Запускаю уведомление группы {group_id} о расписании...")
                total, failed = await notify_students_by_group_repos(
                    group_id, window.text, repos, self.__bot
                )
                logger.debug(
                    f"Уведомление группы закончено. Успешно отправлено: {total - failed}/{total}"
                )

    async def find_group_ids_in_replacement_schedules(
        self, day: date, repos: DBRepositories
    ) -> set[int]:
        """Возвращает ID групп, у которых на указанный день есть замены."""

        replacements = await repos.replacement_schedule.get_by_day(day)
        return {item.group_id for item in replacements}

    async def find_schedules(
        self,
        day: date,
        time_: time,
        replacement_groups: set[int],
        repos: DBRepositories,
    ) -> list[tuple[Schedule, Schedule | None]]:
        """Ищет базовые пары, граничащие с указанным временем (начало/конец)."""

        result: list[tuple[Schedule, Schedule | None]] = []
        lessons = await repos.schedule.get_lessons_by_boundary_time(
            day, len(get_week_stars(day)), time_
        )

        for item in lessons:
            if item.group_id in replacement_groups:
                continue

            next_lesson = None
            if item.class_.end_at == time_:
                upcoming = await repos.schedule.get_upcoming_group_lessons(
                    item.group_id, day, item.stars, item.class_.end_at
                )
                next_lesson = upcoming[0] if upcoming else None

            result.append((item, next_lesson))
        return result

    async def find_replacement_schedules(
        self, day: date, time_: time, repos: DBRepositories
    ) -> list[tuple[ReplacementSchedule, ReplacementSchedule | None]]:
        """Ищет пары по заменам, граничащие с указанным временем."""

        result: list[tuple[ReplacementSchedule, ReplacementSchedule | None]] = []
        lessons = await repos.replacement_schedule.get_lessons_by_boundary_time(
            day, time_
        )

        for item in lessons:
            next_lesson = None
            if item.class_.end_at == time_:
                upcoming = await repos.replacement_schedule.get_upcoming_group_lessons(
                    item.group_id, day, item.class_.end_at
                )
                next_lesson = upcoming[0] if upcoming else None

            result.append((item, next_lesson))
        return result

    def prepare_student_data_notification(
        self,
        targets: list[tuple[ScheduleItem, ScheduleItem | None]],
        repos: DBRepositories,
        target_time: time,
    ) -> Generator[tuple[int, InfoWindow]]:
        """Формирует список сообщений (окон) для рассылки студентам."""

        for schedule, next_schedule in targets:
            cls = schedule.class_
            is_start = cls.start_at == target_time

            window = (
                notification_start_at_window(
                    cls.number,
                    schedule.academic_subject.name,
                    cls.start_at,
                    schedule.audience.name,
                )
                if is_start
                else notification_end_at_window(
                    cls.number,
                    schedule.academic_subject.name,
                    cls.end_at,
                    schedule.audience.name,
                    next_schedule,
                )
            )
            yield schedule.group_id, window
