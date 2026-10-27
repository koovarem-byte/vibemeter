"""Предупреждения за нарушения: фото без лица/чужое, мат в вопросах и ответах,
неадекватная анкета. Счёт общий: два предупреждения, на третье — бан
и карточка админу.
"""

import logging

from database import add_strike, get_user, set_banned
import ui

MAX_WARNINGS = 2


async def punish(bot, user_id: int, total: int, reason: str, detail: str = "") -> str:
    """По общему числу предупреждений: текст человеку; на третье — бан."""
    total = max(total, 1)  # записи ещё нет (до согласия) — считаем первым
    if total <= MAX_WARNINGS:
        return ui.strike_warning(reason, total, MAX_WARNINGS)
    await set_banned(user_id, True)
    try:
        import admin  # admin импортирует handlers, а те — этот модуль
        person = await get_user(user_id)
        note = f"🚫 <b>Автобан</b>: {total}-е нарушение — {reason}"
        if detail:
            note += f"\n«{ui.esc(detail[:200])}»"
        await admin.send_card(bot, person, note=note)
    except Exception:
        logging.exception("Не удалось отправить автобан админу %s", user_id)
    return ui.strike_banned(reason)


async def give(bot, user_id: int, kind: str, reason: str, detail: str = "") -> str:
    """+1 предупреждение вида kind (photo / question / profile)."""
    total = await add_strike(user_id, kind)
    return await punish(bot, user_id, total, reason, detail)


def is_ban_text(text: str) -> bool:
    return text.startswith(ui.BANNED_PREFIX)
