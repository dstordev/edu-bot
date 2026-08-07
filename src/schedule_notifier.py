from datetime import UTC, date, datetime, time, timedelta

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
from utils.schedule import get_week_stars


class ScheduleNotifier:
    """
    Этот класс должен будет контролировать уведомление студентов групп на основе времени начала и конца занятий.

    У него есть доступы к методам телеграм бота и таблицам.
    """

    def __init__(
        self, bot: Bot, async_sessionmaker: async_sessionmaker[AsyncSession]
    ) -> None:
        self.__bot = bot
        self.__async_sessionmaker = async_sessionmaker
        self.__scheduler = AsyncIOScheduler()

    def run_monitor(self) -> None:
        self.__scheduler.add_job(self.check_class_and_notify, "interval", minutes=1)
        self.__scheduler.start()

    async def check_class_and_notify(self) -> None:
        """
        Эта функция уведомит студентов из групп, у которых через 5 минут начнется или закончится занятие. Она учитывает расписание замен и статичное расписание.
        """

        cur_logger = logger.bind()

        cur_logger.info("Начинаю проверку за 5 минут до начала/конца пары...")

        # Дата и время сейчас
        dt_now: datetime = datetime.now(UTC).astimezone()
        # (Дата и время сейчас) + 5 мин.
        dt_now_plus_5m: datetime = dt_now + timedelta(minutes=5)
        # Дата сейчас + 5 мин.
        day_now_plus_5m: date = dt_now_plus_5m.date()
        # Время сейчас + 5 мин.
        time_now_plus_5m: time = dt_now_plus_5m.time()
        # Обнуляем секунды и микросекунды - это костыль
        time_now_plus_5m = time_now_plus_5m.replace(second=0, microsecond=0)

        cur_logger.debug(f"Время через 5 минут: {time_now_plus_5m}")

        async with self.__async_sessionmaker() as session:
            dbrepositories = DBRepositories(session)

            cur_logger.debug("Проверяю рабочий ли сегодня день...")

            if (
                await is_non_working_day(
                    day=day_now_plus_5m, dbrepositories=dbrepositories
                )
                is True
            ):
                cur_logger.debug("-> Сегодня нерабочий день. Проверка окончена.")
                return
            else:
                cur_logger.debug("-> Сегодня рабочий день")

            # Список, где хранится собранная информация о расписании для групп.
            schedule_and_next_list: list[
                tuple[
                    ReplacementSchedule | Schedule,
                    ReplacementSchedule | Schedule | None,
                ]
            ] = []

            cur_logger.debug(
                "Смотрю какие группы сегодня учатся по расписанию замен..."
            )

            group_ids_in_replacement_schedules = (
                await self.find_group_ids_in_replacement_schedules(
                    day_now_plus_5m, dbrepositories
                )
            )
            if len(group_ids_in_replacement_schedules) > 0:
                cur_logger.debug(
                    f"-> Группы сегодня в расписании замен: {group_ids_in_replacement_schedules}"
                )
            else:
                cur_logger.debug(
                    "-> Сегодня ни одна группа не учится по расписанию замен"
                )

            cur_logger.debug(f"Ищу статичные расписания на {time_now_plus_5m}...")
            # Ищем статичные расписания на сегодня, с конкретными занятиями.

            # (Статичное, Группа 1, пара 1)
            # (Статичное, Группа 2, пара 1)
            # (Статичное, Группа 3, пара 1)
            schedules = await self.find_schedules(
                day_now_plus_5m,
                time_now_plus_5m,
                group_ids_in_replacement_schedules,
                dbrepositories,
            )
            schedule_and_next_list.extend(schedules)
            if len(schedules) <= 0:
                cur_logger.debug(
                    f"-> Не удалось найти статичные расписания на {time_now_plus_5m}"
                )

            if len(group_ids_in_replacement_schedules) > 0:
                # Ищем расписание замен на сегодня, с конкретными занятиями.
                cur_logger.debug(f"Ищу расписание замен на {time_now_plus_5m}...")

                # (Замены, Группа 1, пара 1)
                # (Замены, Группа 2, пара 1)
                # (Замены, Группа 3, пара 1)
                replacement_schedules = await self.find_replacement_schedules(
                    time_now_plus_5m, day_now_plus_5m, dbrepositories
                )
                schedule_and_next_list.extend(replacement_schedules)
                if len(replacement_schedules) <= 0:
                    cur_logger.debug(
                        f"-> Не удалось найти расписание замен на {time_now_plus_5m}"
                    )

            if len(schedule_and_next_list) <= 0:
                cur_logger.info(
                    "-> Не удалось найти конец или начало любой пары через 5 минут. Проверка окончена."
                )
                return

            cur_logger.debug("Подготавливаю сообщения для отправки студентам...")
            notifications_to_send = await self.prepare_student_data_notification(
                schedule_and_next_list, dbrepositories, time_now_plus_5m
            )

        cur_logger.info("Отправляю уведомления студентам...")
        # Проходимся по списку с уведомлениями, и отправляем его.
        for student_telegram_id, notify_window in notifications_to_send:
            try:
                await self.telegram_notify_student(student_telegram_id, notify_window)
                cur_logger.success(
                    f"-> Сообщение доставлено студенту {student_telegram_id}."
                )
            except Exception as ex:
                cur_logger.error(
                    f"-> При отправке сообщения студенту произошла неизвестная ошибка: {ex}"
                )
        cur_logger.success("-> Проверка окончена.")

    async def find_group_ids_in_replacement_schedules(
        self, day: date, dbrepositories: DBRepositories
    ) -> set[int]:
        # Какие группы сегодня учатся по расписанию замен.
        groups_in_replacement_schedules: set[int] = set()
        for (
            replacement_schedule
        ) in await dbrepositories.replacement_schedule.get_by_day(day):
            groups_in_replacement_schedules.add(replacement_schedule.group_id)
        return groups_in_replacement_schedules

    async def find_schedules(
        self,
        day: date,
        time_: time,
        groups_in_replacement_schedules: set[int],
        dbrepositories: DBRepositories,
    ) -> list[tuple[Schedule, Schedule | None]]:
        """
        Пытается найти пары в расписаниях, которые начнутся/закончатся в переданное время
        """

        target_groups_and_info: list[tuple[Schedule, Schedule | None]] = []

        # Ищем статичные расписания на сегодня, с конкретными занятиями.
        schedules = await dbrepositories.schedule.get_lessons_by_boundary_time(
            day,
            len(get_week_stars(day)),
            time_,
        )

        # Пройдемся по полученным расписаниям.
        for schedule in schedules:
            class_end_at = schedule.class_.end_at

            # Если у этой группы сегодня расписание в заменах, то не уведомляем её по статичному расписанию. Скипаем.
            if schedule.group_id in groups_in_replacement_schedules:
                continue

            next_schedule: Schedule | ReplacementSchedule | None = None
            if class_end_at == time_:
                result = await dbrepositories.schedule.get_upcoming_group_lessons(
                    schedule.group_id,
                    day,
                    schedule.stars,
                    class_end_at,
                )
                if len(result) > 0:
                    next_schedule = result[0]

            target_groups_and_info.append((schedule, next_schedule))
        return target_groups_and_info

    async def find_replacement_schedules(
        self, time_: time, day: date, dbrepositories: DBRepositories
    ) -> list[tuple[ReplacementSchedule, ReplacementSchedule | None]]:
        """
        Пытается найти пары в расписаниях замен, которые начнутся/закончатся в переданное время
        """

        schedule_and_next_list: list[
            tuple[ReplacementSchedule, ReplacementSchedule | None]
        ] = []

        # Ищем у всех групп, любые пары, которые начнутся/закончатся в переданное время
        replacement_schedules = (
            await dbrepositories.replacement_schedule.get_lessons_by_boundary_time(
                day, time_
            )
        )

        # Пройдемся по полученным расписаниям.
        for schedule in replacement_schedules:
            class_end_at = schedule.class_.end_at

            # Если эта пара заканчивается, то сразу ищем информацию о следующей
            next_schedule: Schedule | ReplacementSchedule | None = None
            if class_end_at == time_:
                result = await dbrepositories.replacement_schedule.get_upcoming_group_lessons(
                    schedule.group_id, day, class_end_at
                )
                if len(result) > 0:
                    next_schedule = result[0]
            schedule_and_next_list.append((schedule, next_schedule))

        return schedule_and_next_list

    async def prepare_student_data_notification(
        self,
        target_groups_and_info: list[
            tuple[ReplacementSchedule | Schedule, ReplacementSchedule | Schedule | None]
        ],
        dbrepositories: DBRepositories,
        iso_t_now_plus_5_min: time,
    ):
        # Список, где хранятся уведомления для отправки
        notifications_to_send: list[tuple[int, InfoWindow]] = []

        for schedule, next_schedule in target_groups_and_info:
            # Пройдемся по каждому студенту и запишем его в список.
            async for student in dbrepositories.student.find_students_by_group(
                schedule.group_id
            ):
                class_start_at = schedule.class_.start_at
                class_end_at = schedule.class_.end_at
                class_number = schedule.class_.number
                academic_subject_name = schedule.academic_subject.name
                audience_name = schedule.audience.name
                # class_type_name: str = schedule.class_type_.name

                if class_start_at == iso_t_now_plus_5_min:
                    notify_window = notification_start_at_window(
                        class_number,
                        academic_subject_name,
                        class_start_at,
                        audience_name,
                    )
                else:
                    notify_window = notification_end_at_window(
                        class_number,
                        academic_subject_name,
                        class_end_at,
                        audience_name,
                        next_schedule,
                    )

                # Вместо отправки уведомления сразу, мы сначала записываем его в список.
                notifications_to_send.append((student.telegram_id, notify_window))

        return notifications_to_send

    async def telegram_notify_student(
        self, student_telegram_id: int, info_window: InfoWindow
    ):
        """
        Эта функция уведомит студента о том, что пара началась или закончилась.
        """

        await info_window.send_window(self.__bot, student_telegram_id)
