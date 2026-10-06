import asyncio
import json
from datetime import datetime

import aiohttp
import websockets
from aiogram import Bot
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.repositories._repositories import DBRepositories
from telegram_bot.utils.html_format import b, blockquote, code, i
from utils.datetime_format import DATE_FORMAT, RU_WEEKDAY_NAMES
from utils.notify_students import notify_students_by_group
from utils.timezones import TZ_MOSCOW

from .parser import NonWorkingDayLessonDTO, ParsedLessonDTO, parse_docx_bytes
from .utils import (
    extract_date_from_filename,
    generate_request_id,
    generate_session,
    unpack_yandex_ws,
)


async def save_replacements_for_group(
    dbrepositories: DBRepositories,
    group_id: int,
    group_name: str,
    lessons_dto: list[ParsedLessonDTO | NonWorkingDayLessonDTO],
) -> int:
    """Сохраняет замены конкретной группы в БД с валидацией сущностей."""

    added_count = 0
    group_lessons = [dto for dto in lessons_dto if group_name in dto.group_name]

    for dto in group_lessons:
        if isinstance(dto, NonWorkingDayLessonDTO):
            await dbrepositories.non_working_day.add(dto.date, group_id)
            added_count += 1
            continue

        class_ = await dbrepositories.class_.find_class_by_time(
            dto.class_start, dto.class_end
        )
        if not class_:
            continue

        subject = await dbrepositories.academic_subject.find_by_name(dto.subject_name)
        if not subject:
            continue

        class_type_id: int | None = None
        if dto.class_type_name is not None and (
            class_type := await dbrepositories.class_type.find_by_name(
                dto.class_type_name
            )
        ):
            class_type_id = class_type.id

        audience_id: int | None = None
        if dto.audience_name is not None and (
            audience := await dbrepositories.audience.find_by_name(dto.audience_name)
        ):
            audience_id = audience.id

        await dbrepositories.replacement_schedule.add(
            date_=dto.date,
            group_id=group_id,
            class_id=class_.id,
            academic_subject_id=subject.id,
            class_type_id=class_type_id,
            audience_id=audience_id,
        )
        added_count += 1

    return added_count


async def get_files(
    study_chat_id: str, session_id: str, user_id: str, limit: int = 41
) -> list[dict[str, str]]:
    """Подключается к WebSocket Яндекса и запрашивает список файлов из чата."""

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:156.0) Gecko/20100101 Firefox/156.0",
        "Origin": "https://telemost.360.yandex.com",
        "Cookie": f"Session_id={session_id}",
    }
    ws_url = (
        "wss://push.yandex.com/v2/subscribe/websocket?"
        "service=messenger-prod%3Aversion5*common%2Bversion5*main&"
        f"session={generate_session()}&client=web_main&user={user_id}"
    )

    try:
        async with (
            asyncio.timeout(10),
            websockets.connect(ws_url, additional_headers=headers) as ws,
        ):
            req_payload = {
                "RequestId": generate_request_id(),
                "ChatId": study_chat_id,
                "Limit": limit,
            }
            await ws.send(
                b"\x01\x93\x00\x03\xa7history\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                + json.dumps(req_payload).encode()
            )

            async for raw_message in ws:
                if not isinstance(raw_message, bytes):
                    continue

                msg_type, data = unpack_yandex_ws(raw_message)
                if msg_type != "history" or not data:
                    continue

                chats = data.get("Chats", [])
                if not chats:
                    return []

                files = []
                messages = chats[0].get("Messages", [])
                for msg in messages:
                    plain = (
                        msg.get("ServerMessage", {})
                        .get("ClientMessage", {})
                        .get("Plain")
                    )
                    if not plain:
                        continue

                    file_info = plain.get("MiscFile", {}).get("FileInfo", {})
                    file_path = file_info.get("Id2")
                    filename = file_info.get("Name")

                    if file_path and filename:
                        files.append({"filename": filename, "file_path": file_path})

                return files

    except TimeoutError:
        logger.error("Таймаут ожидания ответа от WebSocket Яндекса")
    except Exception as e:
        logger.error(f"Ошибка при работе с WebSocket: {e}")

    return []


async def download_file(file_path: str, session_id: str) -> bytes:
    """Скачивает файл из шлюза мессенджера напрямую в оперативную память."""
    clean_path = file_path.lstrip("/")
    if clean_path.startswith("http"):
        url = clean_path
    elif clean_path.startswith("file_shortterm"):
        url = f"https://files.messenger.yandex.com/{clean_path}"
    else:
        url = f"https://files.messenger.yandex.com/file_shortterm/{clean_path}"

    timeout = aiohttp.ClientTimeout(total=60)
    async with (
        aiohttp.ClientSession(
            cookies={"Session_id": session_id}, timeout=timeout
        ) as session,
        session.get(
            url,
            params={"attach": "true"},
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:156.0) Gecko/20100101 Firefox/156.0",
                "Accept": "*/*",
            },
        ) as response,
    ):
        response.raise_for_status()
        return await response.read()


async def check_schedule_updates(
    study_chat_id: str,
    session_id: str,
    user_id: str,
    redis: Redis,
    async_sessmaker: async_sessionmaker[AsyncSession],
    bot: Bot,
) -> None:
    """Основной пайплайн одной проверки."""

    files = await get_files(study_chat_id, session_id, user_id)
    if not files:
        return

    # Получаем группу из БД
    async with async_sessmaker() as session:
        repos = DBRepositories(session)
        groups = await repos.group.get_groups()
        if len(groups) <= 0:
            logger.error("[Worker] Не найдено ни одной группы в БД!")
            return

    today = datetime.now(TZ_MOSCOW).date()

    for file in files:
        filename = file["filename"]
        file_path = file["file_path"]
        file_date = extract_date_from_filename(filename)

        # Пропускаем старые файлы
        if file_date and file_date < today:
            continue

        # ПРОВЕРКА В REDIS: обрабатывали ли мы уже этот файл?
        cache_key = f"processed_schedule_file:{file_path}"
        if await redis.exists(cache_key):
            continue

        logger.info(f"[Worker] Обнаружен новый файл: {filename}. Скачиваем...")
        try:
            file_bytes = await download_file(file_path, session_id)
        except Exception as e:
            logger.error(f"[Worker] Ошибка при скачивании {filename}: {e}")
            continue

        # ВАЖНО: синхронный парсер запускаем в отдельном потоке
        schedule_date, parsed_dtos = await asyncio.to_thread(
            parse_docx_bytes, file_bytes, file_date
        )

        if not schedule_date:
            logger.warning(f"[Worker] Не удалось определить дату для файла {filename}")
            # Помечаем файл как просмотренный на 1 день, чтобы не циклиться на битом файле
            await redis.set(cache_key, "invalid", ex=86400)
            continue

        # TODO: Возможно можно улушчить логику проходки по группам
        for group in groups:
            # Запись в БД в транзакции
            async with async_sessmaker.begin() as session:
                repos = DBRepositories(session)

                # Если на этот день у группы уже были записаны замены — очищаем их перед обновлением
                # (так как файл мог быть перезалит деканатом с исправлениями)
                await repos.replacement_schedule.delete_by_group_and_date(
                    group.id, schedule_date
                )
                await repos.non_working_day.delete(schedule_date, group.id)

                added_count = await save_replacements_for_group(
                    dbrepositories=repos,
                    group_id=group.id,
                    group_name=group.name,
                    lessons_dto=parsed_dtos,
                )

            # Помечаем файл в Redis как успешно обработанный (TTL 5 дней)
            await redis.set(cache_key, "processed", ex=432000)

            if added_count > 0:
                logger.success(
                    f"[Worker] Добавлено {added_count} замен для {group.name} на {schedule_date}!"
                )

                # Рассылка сообщений студентам
                logger.debug(
                    "[Worker] Начинаю уведомление студентов о новом расписании..."
                )
                # подготовка данных для красивой даты
                d = {0: "сегодня", -1: "завтра", -2: "послезавтра"}
                now_d = datetime.now(TZ_MOSCOW).date()
                ed = now_d - schedule_date
                d_name = d.get(ed.days)

                weekday_name = RU_WEEKDAY_NAMES[schedule_date.weekday()].lower()
                schedule_date_beuatufy = code(f"{schedule_date.strftime(DATE_FORMAT)}")
                ####

                total, failed = await notify_students_by_group(
                    group.id,
                    b(
                        f"😺 Обновлено расписание\n"
                        f"{blockquote(f'Дата: {schedule_date_beuatufy} {i(f"({(str(d_name) + ', ') if d_name else ''}{weekday_name})")}')}"
                    ),
                    async_sessmaker,
                    bot,
                )
                logger.debug(
                    f"[Worker] Уведомление студентов закончено. Успешно отправлено: {total - failed}/{total}"
                )
            else:
                logger.info(
                    f"[Worker] В файле {filename} замен для группы {group.name} не найдено."
                )
