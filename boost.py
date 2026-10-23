"""Награда за друга: анкета пригласившего сутки показывается первой.

Даётся, когда приглашённый заполнил анкету (один раз за каждого).
"""

from datetime import datetime, timezone

from database import add_boost

HOURS = 24


def is_boosted(person) -> bool:
    until = person.get("boost_until")
    return bool(until) and until > datetime.now(timezone.utc)


async def reward_inviter(inviter_id: int):
    return await add_boost(inviter_id, HOURS)
