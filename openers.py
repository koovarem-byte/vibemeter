"""Подсказки первой фразы при взаимном вайбе: по общим интересам и городу."""

import random

BY_INTEREST = (
    "Вижу, ты тоже про «{i}». Как давно этим увлекаешься?",
    "«{i}» — это круто. Что в этом тебе нравится больше всего?",
    "Расскажи про «{i}»: с чего начать, если я новичок?",
    "Если бы про «{i}» надо было выбрать одну вещь, какая бы это была?",
)

BY_CITY = (
    "Мы из одного города ({c})! Какое у тебя любимое место здесь?",
    "Земляк ({c})! Куда сходить на выходных, посоветуешь?",
)

GENERIC = (
    "Привет! Вайб совпал, это знак. Как проходит твой день?",
    "Привет! Если бы мы выбирали место для первой встречи, куда бы позвал(а)?",
    "Привет! Утро или ночь, какой ты человек?",
    "Привет! Что последнее тебя по-настоящему порадовало?",
)


def make_openers(common: list[str], city: str | None, same_city: bool, seed: int) -> list[str]:
    """До трёх фраз. seed делает набор стабильным для пары."""
    rnd = random.Random(seed)
    result = []
    for interest in rnd.sample(list(common), min(len(common), 2)):
        result.append(rnd.choice(BY_INTEREST).format(i=interest))
    if same_city and city:
        result.append(rnd.choice(BY_CITY).format(c=city.strip()))
    pool = list(GENERIC)
    rnd.shuffle(pool)
    for text in pool:
        if len(result) >= 3:
            break
        result.append(text)
    return result[:3]
