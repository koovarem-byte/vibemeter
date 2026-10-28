"""«Позвать подругу»: t.me/бот?start=ref_<id>.

Подруга засчитывается, когда она девушка, анкета с фото, не в бане и
заходила в день ПОСЛЕ регистрации. Проверяем при каждой её активности
(только тех, кто ещё не засчитан, — список в памяти) и раз в час фоном.
За каждые 3 засчитанные подруги пригласившему VIP на 7 дней.
"""

import asyncio
import logging
from urllib.parse import quote

from database import (
    count_qualified,
    grant_referral_vip,
    pending_invitees,
    qualify_referrals,
)
import ui

GOAL = 3
CHECK_EVERY = 3600

# приглашённые, которых ещё могут засчитать: проверка при активности без лишних запросов
_pending: set[int] = set()


def link(bot_username: str, user_id: int) -> str:
    return f"https://t.me/{bot_username}?start=ref_{user_id}"


def share_url(ref_link: str) -> str:
    return f"https://t.me/share/url?url={quote(ref_link)}&text={quote(ui.INVITE_SHARE_TEXT)}"


def add_pending(invitee: int):
    _pending.add(invitee)


def is_pending(user_id: int) -> bool:
    return user_id in _pending


async def _reward(bot, qualified: list[dict]):
    for row in qualified:
        _pending.discard(row["invitee"])
    for inviter in {row["inviter"] for row in qualified}:
        try:
            if await grant_referral_vip(inviter):
                await bot.send_message(inviter, ui.INVITE_REWARD)
        except Exception:
            logging.warning("Рефералка: не удалось наградить %s", inviter)


async def check(bot, invitee: int):
    """Активность приглашённой: вдруг её уже можно засчитать."""
    if invitee not in _pending:
        return
    await _reward(bot, await qualify_referrals(invitee))


async def check_all(bot):
    global _pending
    _pending = await pending_invitees()
    if _pending:
        await _reward(bot, await qualify_referrals())


async def progress(user_id: int) -> int:
    return await count_qualified(user_id)


async def loop(bot):
    """Раз в час. Если ждать некого — базу не трогаем (не будим Neon)."""
    first = True
    while True:
        try:
            if first or _pending:
                await check_all(bot)
            first = False
        except asyncio.CancelledError:
            raise
        except Exception:
            logging.exception("Рефералка: фоновая проверка упала")
        await asyncio.sleep(CHECK_EVERY)
