"""VIP: 💎 в анкете, анкета выше в ленте, «Кто меня лайкнул».

Девушкам — навсегда после анкеты, пригласившему — 7 дней за каждые
3 засчитанные подруги (referral.py).
"""

from datetime import datetime, timezone


def is_vip(person) -> bool:
    until = person.get("vip_until") if person else None
    return bool(until) and until > datetime.now(timezone.utc)


def is_forever(person) -> bool:
    until = person.get("vip_until") if person else None
    return bool(until) and until.year >= 2099
