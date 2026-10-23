"""Общий прогресс города: «Псков: 37 из 100».

Только настоящие числа: анкеты 18+ без бана из базы. Приглашённый друг
двигает шкалу всего города, а не копит личные бонусы.
"""

import re

from database import city_counts

GOALS = (100, 250, 500, 1000, 2500, 5000, 10000)

ALIASES = {
    "спб": "санкт петербург",
    "питер": "санкт петербург",
    "санкт петербург": "санкт петербург",
    "мск": "москва",
    "нн": "нижний новгород",
    "екб": "екатеринбург",
}


def normalize(city: str | None) -> str:
    text = (city or "").lower().replace("ё", "е")
    text = re.sub(r"^(г\.|город)\s*", "", text.strip())
    text = re.sub(r"[-\s]+", " ", text).strip(" .")
    return ALIASES.get(text, text)


def goal_for(count: int) -> int:
    return next((g for g in GOALS if count < g), GOALS[-1])


async def progress(city: str | None) -> dict | None:
    key = normalize(city)
    if not key:
        return None
    count = sum(n for name, n in await city_counts() if normalize(name) == key)
    return {"name": (city or "").strip(), "count": count, "goal": goal_for(count)}
