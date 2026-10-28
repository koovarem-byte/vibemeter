"""Рассылка всем: личная строка по состоянию человека + голосование за функцию.

Запускает только админ (/admin → «Рассылка»). Каждому — не больше одного
раза на кампанию (broadcast_log), после перезапуска докатывается с места
остановки. Заблокировавшим бота больше не пишем.
"""

import asyncio
import logging
import time

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import LinkPreviewOptions

from database import (
    broadcast_targets,
    campaign_targets,
    claim_broadcast,
    get_admin_stats,
    mark_broadcast,
    set_news_notify,
)
from keyboards import broadcast_keyboard, campaign_keyboard, sorry_keyboard
import referral
import stickers
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


# =========================================================
# РАССЫЛКА С ПРЕДПРОСМОТРОМ: сегмент → шаблон (ui.CAMPAIGNS) → «Отправить»
# Кампания = ключ шаблона: кто её уже получил, повторно не получит.
# =========================================================

RATE = 25  # сообщений в секунду, не быстрее (лимит Telegram ~30)
_last_send = 0.0


async def _throttle():
    global _last_send
    wait = _last_send + 1 / RATE - time.monotonic()
    if wait > 0:
        await asyncio.sleep(wait)
    _last_send = time.monotonic()


async def _call(fn, *args, **kwargs):
    """Запрос к Telegram с паузой по лимиту и повтором после RetryAfter."""
    for attempt in range(3):
        await _throttle()
        try:
            return await fn(*args, **kwargs)
        except TelegramRetryAfter as e:
            if attempt == 2:
                raise
            await asyncio.sleep(e.retry_after + 1)


async def send_campaign(bot, chat_id: int, key: str, bot_username: str, ref_link: str | None = None):
    """Ровно то, что получит человек: стикер + текст + кнопка.
    ref_link — чья ссылка подставится (по умолчанию самого получателя)."""
    tpl = ui.CAMPAIGNS[key]
    ref_link = ref_link or referral.link(bot_username, chat_id)
    if tpl["sticker"]:
        await _call(stickers.send, bot, chat_id, tpl["sticker"])
    await _call(
        bot.send_message,
        chat_id,
        tpl["text"].format(ref_link=ref_link),
        reply_markup=campaign_keyboard(tpl["button"], bot_username),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )


async def deliver(bot, user_id: int, key: str, bot_username: str) -> str:
    """Одному человеку один раз: sent / blocked / error / skip (уже получал)."""
    if not await claim_broadcast(key, user_id):
        return "skip"
    try:
        await send_campaign(bot, user_id, key, bot_username)
        status = "sent"
    except TelegramForbiddenError:
        await set_news_notify(user_id, False)
        status = "blocked"
    except Exception:
        logging.warning("Рассылка %s: не отправилось %s", key, user_id)
        status = "error"
    await mark_broadcast(key, user_id, status)
    return status


def start_campaign(bot, report_to: int, key: str, segment: str) -> bool:
    """Запускает в фоне. False, если какая-то рассылка уже идёт."""
    global _running, _task
    if _running:
        return False
    _running = True
    _task = asyncio.create_task(run_campaign(bot, report_to, key, segment))
    return True


async def run_campaign(bot, report_to: int, key: str, segment: str):
    global _running
    counts = {"sent": 0, "blocked": 0, "error": 0, "skip": 0}
    try:
        bot_username = (await bot.me()).username
        for user_id in await campaign_targets(key, segment):
            counts[await deliver(bot, user_id, key, bot_username)] += 1
    except Exception:
        logging.exception("Рассылка %s оборвалась", key)
    finally:
        _running = False
    await bot.send_message(
        report_to,
        f"📨 Рассылка «{ui.CAMPAIGNS[key]['title']}» · {ui.SEGMENTS[segment]} готова\n\n"
        f"✅ Отправлено: <b>{counts['sent']}</b>\n"
        f"🚫 Заблокировали бота: {counts['blocked']}\n"
        f"⚠️ Ошибки: {counts['error']}",
    )
