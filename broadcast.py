"""Рассылка всем: личная строка по состоянию человека + голосование за функцию.

Запускает только админ (/admin → «Рассылка»). Каждому — не больше одного
раза на кампанию (broadcast_log), после перезапуска докатывается с места
остановки. Заблокировавшим бота больше не пишем.
"""

import asyncio
import logging

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from database import (
    broadcast_targets,
    claim_broadcast,
    get_admin_stats,
    mark_broadcast,
    set_news_notify,
)
from keyboards import broadcast_keyboard, sorry_keyboard
import ui

# новая рассылка = новый ключ (и новый текст в ui.broadcast_text)
CAMPAIGN = "vote1"
# «Мы снова в строю» после сбоя 27.10
SORRY = "sorry1"

_running = False
_task = None


def is_running() -> bool:
    return _running


def message_for(campaign: str, person: dict, total: int, bot_username: str):
    """Текст и кнопки рассылки для человека."""
    if campaign == SORRY:
        return ui.SORRY_TEXT, sorry_keyboard(person, bot_username)
    return ui.broadcast_text(person, total), broadcast_keyboard(person, bot_username)


def start(bot, report_to: int, campaign: str = CAMPAIGN) -> bool:
    """Запускает рассылку в фоне. False, если она уже идёт."""
    global _running, _task
    if _running:
        return False
    _running = True
    _task = asyncio.create_task(run(bot, report_to, campaign))
    return True


async def send_one(bot, person: dict, total: int, bot_username: str, campaign=CAMPAIGN) -> str:
    """Отправляет одному. Возвращает статус: sent / blocked / error / skip."""
    if not await claim_broadcast(campaign, person["telegram_id"]):
        return "skip"
    text, keyboard = message_for(campaign, person, total, bot_username)
    status = "error"
    for _ in range(2):
        try:
            await bot.send_message(person["telegram_id"], text, reply_markup=keyboard)
            status = "sent"
            break
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
        except TelegramForbiddenError:
            # бот заблокирован — новости больше не шлём
            await set_news_notify(person["telegram_id"], False)
            status = "blocked"
            break
        except Exception:
            logging.warning("Рассылка: не отправилось %s", person["telegram_id"])
            break
    await mark_broadcast(campaign, person["telegram_id"], status)
    return status


async def run(bot, report_to: int, campaign: str = CAMPAIGN):
    """Отправляет всем, кому ещё не отправляли, и присылает итог админу."""
    global _running
    counts = {"sent": 0, "blocked": 0, "error": 0, "skip": 0}
    try:
        total = (await get_admin_stats())["total_users"]
        bot_username = (await bot.me()).username
        for person in await broadcast_targets(campaign):
            counts[await send_one(bot, person, total, bot_username, campaign)] += 1
            await asyncio.sleep(0.05)  # ~20 в секунду, лимит Telegram 30
    except Exception:
        logging.exception("Рассылка оборвалась")
    finally:
        _running = False
    await bot.send_message(
        report_to,
        f"📣 Рассылка готова: доставлено {counts['sent']}, "
        f"заблокировали бота {counts['blocked']}, ошибок {counts['error']}",
    )
