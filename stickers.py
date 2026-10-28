"""Стикеры рассылок и мэтча: assets/stickers/<имя>.webm (анимированные неоновые,
нарисованы make_stickers.py), запасной — <имя>.webp (статичный кадр).

Первый раз файл загружается в Telegram, его file_id сохраняется в app_state
под ключом sticker_<имя>:<хеш файла> — новый файл сам загрузится заново.
Ничего не вышло — сообщение уходит без стикера.
"""

import hashlib
import logging
from pathlib import Path

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile

from database import get_app_state, set_app_state

DIR = Path(__file__).resolve().parent / "assets" / "stickers"
EXTENSIONS = (".webm", ".webp")  # сначала анимация

_cache: dict[str, str] = {}
_rejected: set[Path] = set()
_missing: set[str] = set()


def _name(name: str) -> str:
    return name if name.startswith("sticker_") else f"sticker_{name}"


def _files(name: str) -> list[Path]:
    return [DIR / f"{name}{ext}" for ext in EXTENSIONS if (DIR / f"{name}{ext}").is_file()]


def _key(path: Path) -> str:
    digest = hashlib.sha1(path.read_bytes()).hexdigest()[:10]
    return f"{path.stem}:{digest}"


async def send(bot, chat_id: int, name: str | None):
    """Отправляет стикер. TelegramForbiddenError (бот заблокирован) пробрасываем:
    рассылке нужно знать, что человек недоступен. Прочие ошибки — без стикера."""
    if not name:
        return None
    name = _name(name)
    files = [p for p in _files(name) if p not in _rejected]
    if not files:
        if name not in _missing:
            _missing.add(name)
            logging.warning("Стикер %s: нет файла в %s, шлём без стикера", name, DIR)
        return None

    for path in files:
        key = _key(path)
        file_id = _cache.get(key) or await get_app_state(key)
        if file_id:
            try:
                msg = await bot.send_sticker(chat_id, file_id)
                _cache[key] = file_id
                return msg
            except TelegramBadRequest:
                logging.warning("Стикер %s: file_id не принят, загружаю файл", key)
                _cache.pop(key, None)
        try:
            msg = await bot.send_sticker(chat_id, FSInputFile(path))
        except TelegramBadRequest as e:
            if "chat" in e.message.lower():
                return None  # дело в получателе, а не в файле
            # например, видео не подошло — пробуем статичный
            logging.warning("Стикер %s: Telegram не принял файл (%s)", path.name, e.message)
            _rejected.add(path)
            continue
        if msg.sticker:
            _cache[key] = msg.sticker.file_id
            await set_app_state(key, msg.sticker.file_id)
        return msg
    return None
