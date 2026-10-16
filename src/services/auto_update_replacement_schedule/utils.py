import json
import re
import secrets
import uuid
from datetime import date

import msgpack
from loguru import logger


def unpack_yandex_ws(raw: bytes) -> tuple[str, dict | None]:
    """
    Распаковывает фрейм Яндекса.
    Возвращает (msg_type, payload_dict) или ('unknown', None).
    """

    if not raw or len(raw) < 2 or raw[0] != 0x01:
        return "unknown", None

    try:
        unpacker = msgpack.Unpacker()
        unpacker.feed(raw[1:])
        header = unpacker.unpack()

        msg_type = (
            header[2] if isinstance(header, list) and len(header) > 2 else "unknown"
        )
        header_end_offset = 1 + unpacker.tell()

    except Exception:
        return "unknown", None

    if msg_type != "history":
        return msg_type, None

    json_idx = raw.find(b'{"', header_end_offset)
    if json_idx == -1:
        return msg_type, None

    try:
        json_bytes = raw[json_idx:]
        payload = json.loads(json_bytes.decode("utf-8"))
        return msg_type, payload
    except Exception as e:
        logger.debug(f"Не удалось распарсить JSON из history-пакета: {e}")
        return msg_type, None


def generate_request_id() -> str:
    """Генерирует уникальный RequestId в формате 8-4-4-8."""
    h = uuid.uuid4().hex
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:24]}"


def generate_session() -> str:
    """Генерирует случайный идентификатор вкладки/сессии в формате 4-4-4-4."""
    h = secrets.token_hex(8)
    return f"{h[:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"


def extract_date_from_filename(filename: str) -> date | None:
    """Извлекает дату в формате dd.mm.YYYY из названия файла."""
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", filename)
    if match:
        day, month, year = map(int, match.groups())
        return date(year, month, day)
    return None
