"""Ситуации для партий: situations.json (правит автор) + добавленные из админки
(/add_situation, таблица custom_situations)."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from database import list_custom_situations

FILE = Path(__file__).resolve().parent / "situations.json"
MSK = timezone(timedelta(hours=3))


def _base() -> list[dict]:
    return json.loads(FILE.read_text(encoding="utf-8"))


async def all_situations() -> list[dict]:
    items = _base()
    keys = {s["key"] for s in items}
    for s in await list_custom_situations():
        if s["key"] not in keys:
            items.append(s)
    return items


async def get(key: str) -> dict | None:
    return next((s for s in await all_situations() if s["key"] == key), None)


async def daily() -> dict:
    """Задача дня: одна ситуация на всех, меняется по Москве (только с репликой от неё)."""
    items = [s for s in await all_situations() if s.get("opening")]
    return items[datetime.now(MSK).date().toordinal() % len(items)]
