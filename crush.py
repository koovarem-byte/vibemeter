"""«Тайная симпатия»: отмечаешь @username, кто нравится.

Человек ничего не узнает, пока не отметит тебя в ответ. Тогда обоим
приходит уведомление. Бот пишет только тем, кто сам пользуется ботом
и сам кого-то отметил, — посторонним никогда.
"""

import logging
import re

import ui
from database import add_crush, find_mutual_crush, get_user
from keyboards import contact_keyboard

LIMIT = 5

_USERNAME = re.compile(r"^[a-z][a-z0-9_]{3,31}$")


def normalize(raw: str) -> str | None:
    """@Name, t.me/Name, https://t.me/Name → name. None, если не похоже на username."""
    text = (raw or "").strip().lower()
    text = re.sub(r"^(https?://)?(www\.)?(t|telegram)\.me/", "", text)
    text = text.lstrip("@").split("?")[0].strip("/")
    return text if _USERNAME.match(text) else None


async def add(bot, user_id: int, raw: str) -> tuple[str, dict | None]:
    """(статус, взаимный человек). Статусы: added, exists, limit, bad, self."""
    username = normalize(raw)
    if not username:
        return "bad", None
    me = await get_user(user_id)
    if me and (me["username"] or "").lower() == username:
        return "self", None

    status = await add_crush(user_id, username, LIMIT)
    if status != "added":
        return status, None

    other = await find_mutual_crush(user_id, username)
    if other:
        for viewer, partner in ((me, other), (other, me)):
            try:
                await bot.send_message(
                    viewer["telegram_id"],
                    ui.crush_mutual(partner),
                    reply_markup=contact_keyboard(partner["username"]),
                )
            except Exception:
                logging.warning("Не удалось сообщить о тайной симпатии %s", viewer["telegram_id"])
    return "added", other
