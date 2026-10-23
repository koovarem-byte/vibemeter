"""Вайб-час: каждый вечер 21:00–22:00 по Москве.

За 10 минут бот напоминает тем, кто заходил последние две недели
и не отключал напоминания. В этот час первыми показываются анкеты
тех, кто сейчас в сети. Число «в сети» всегда настоящее.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram.exceptions import TelegramForbiddenError

import ui
from database import (
    claim_once,
    count_online,
    set_vibe_hour_notify,
    vibe_hour_recipients,
)
from keyboards import vibe_hour_keyboard

MSK = timezone(timedelta(hours=3))  # в Москве нет перехода на летнее время
START_HOUR, END_HOUR = 21, 22
NOTIFY_BEFORE_MIN = 10
ONLINE_MIN = 15          # «в сети» — заходил за последние 15 минут
RECIPIENT_DAYS = 14


def now_msk() -> datetime:
    return datetime.now(MSK)


def is_active(now: datetime | None = None) -> bool:
    now = now or now_msk()
    return START_HOUR <= now.hour < END_HOUR


def is_online(person) -> bool:
    seen = person.get("last_seen") if hasattr(person, "get") else person["last_seen"]
    return bool(seen) and datetime.now(timezone.utc) - seen < timedelta(minutes=ONLINE_MIN)


def minutes_to_start(now: datetime | None = None) -> int:
    now = now or now_msk()
    start = now.replace(hour=START_HOUR, minute=0, second=0, microsecond=0)
    if now >= start:
        start += timedelta(days=1)
    return int((start - now).total_seconds() // 60)


async def status() -> dict:
    return {
        "active": is_active(),
        "starts_in": minutes_to_start(),
        "online": await count_online(ONLINE_MIN),
        "start": f"{START_HOUR}:00",
        "end": f"{END_HOUR}:00",
    }


async def notify_all(bot):
    online = await count_online(ONLINE_MIN)
    text = ui.vibe_hour_soon(online)
    sent = 0
    for user_id in await vibe_hour_recipients(RECIPIENT_DAYS):
        try:
            await bot.send_message(user_id, text, reply_markup=vibe_hour_keyboard())
            sent += 1
        except TelegramForbiddenError:
            # бот заблокирован — больше не пишем
            await set_vibe_hour_notify(user_id, False)
        except Exception:
            logging.warning("Вайб-час: не отправилось %s", user_id)
        await asyncio.sleep(0.05)  # лимиты Telegram
    logging.info("Вайб-час: напоминание ушло %s людям", sent)


async def loop(bot):
    """Фоновая задача: раз в 30 секунд смотрит на часы."""
    while True:
        try:
            now = now_msk()
            if 0 < minutes_to_start(now) <= NOTIFY_BEFORE_MIN:
                if await claim_once("vibe_hour_notified", now.date().isoformat()):
                    await notify_all(bot)
        except Exception:
            logging.exception("Вайб-час: ошибка в цикле")
        await asyncio.sleep(30)
