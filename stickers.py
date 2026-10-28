"""Стикеры из assets/stickers/<имя>.webp.

Первый раз файл загружается в Telegram, его file_id сохраняется в
app_state (sticker_<имя>), дальше шлём по file_id. Нет файла — стикер
просто пропускаем, сообщение уходит без него.
"""

import logging
from pathlib import Path

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile

from database import get_app_state, set_app_state

DIR = Path(__file__).resolve().parent / "assets" / "stickers"

_cache: dict[str, str] = {}
_missing: set[str] = set()


def _key(name: str) -> str:
    return name if name.startswith("sticker_") else f"sticker_{name}"


def _file(name: str) -> Path | None:
    for candidate in (name, _key(name), name.removeprefix("sticker_")):
        path = DIR / f"{candidate}.webp"
        if path.is_file():
            return path
    return None


async def send(bot, chat_id: int, name: str | None):
    """Отправляет стикер. TelegramForbiddenError (бот заблокирован) пробрасываем:
    рассылке нужно знать, что человек недоступен. Прочие ошибки — молча без стикера."""
    if not name:
        return None
    key = _key(name)
    file_id = _cache.get(key) or await get_app_state(key)
    if file_id:
        try:
            msg = await bot.send_sticker(chat_id, file_id)
            _cache[key] = file_id
            return msg
        except TelegramBadRequest:
            # file_id протух (другой бот/токен) — загрузим файл заново
            logging.warning("Стикер %s: file_id не принят, загружаю файл", key)
            _cache.pop(key, None)

    path = _file(name)
    if not path:
        if key not in _missing:
            _missing.add(key)
            logging.warning("Стикер %s: нет файла в %s, шлём без стикера", key, DIR)
        return None
    try:
        msg = await bot.send_sticker(chat_id, FSInputFile(path))
    except TelegramBadRequest:
        logging.warning("Стикер %s: Telegram не принял файл", key)
        return None
    if msg.sticker:
        _cache[key] = msg.sticker.file_id
        await set_app_state(key, msg.sticker.file_id)
    return msg
