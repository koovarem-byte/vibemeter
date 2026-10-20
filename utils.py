from aiogram.types import Message


def normalize_interests(text: str) -> str:
    """
    Приводит интересы к нормальному виду.

    Например:
    "баскетбол, Музыка, баскетбол"
    ->
    "баскетбол, музыка"
    """

    interests = []

    for item in text.split(","):
        item = item.strip()

        if not item:
            continue

        item = item.lower()

        if item not in interests:
            interests.append(item)

    return ", ".join(interests[:10])


def get_common_interests(
    first_interests: str | None,
    second_interests: str | None,
) -> list[str]:

    first = {
        item.strip().lower()
        for item in (first_interests or "").split(",")
        if item.strip()
    }

    second = {
        item.strip().lower()
        for item in (second_interests or "").split(",")
        if item.strip()
    }

    return sorted(first & second)


def format_common_interests(
    interests: list[str],
) -> str:

    if not interests:
        return "Пока общих интересов не нашли"

    return "\n".join(
        f"• {item.capitalize()}"
        for item in interests
    )


def valid_name(name: str) -> bool:
    name = name.strip()

    return (
        len(name) >= 2
        and len(name) <= 30
    )


MIN_AGE = 18
MAX_AGE = 99


def is_adult(age) -> bool:
    """Бот только для 18+. Пустой возраст — не взрослый."""
    return age is not None and age >= MIN_AGE


def valid_age(age: str) -> bool:
    if not age.isdigit():
        return False

    value = int(age)

    return MIN_AGE <= value <= MAX_AGE


def valid_city(city: str) -> bool:
    city = city.strip()

    return (
        len(city) >= 2
        and len(city) <= 50
    )


def valid_description(description: str) -> bool:
    description = description.strip()

    return (
        len(description) <= 500
    )


async def safe_delete(message: Message):
    try:
        await message.delete()
    except Exception:
        pass