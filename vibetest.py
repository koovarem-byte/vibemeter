"""«Проверь вайб с другом»: короткий тест без анкеты.

Автор отвечает на 7 вопросов «что выберешь» и шлёт ссылку
t.me/бот?start=vt_<код>. Друг отвечает на те же вопросы,
оба видят процент совпадения.
"""

import random
import secrets

from games import GAMES

QUESTIONS_COUNT = 7


def new_questions() -> list[int]:
    return random.sample(range(len(GAMES)), QUESTIONS_COUNT)


def new_code() -> str:
    return secrets.token_urlsafe(6)


def valid_questions(questions) -> bool:
    return (
        isinstance(questions, list)
        and len(questions) == QUESTIONS_COUNT
        and len(set(questions)) == QUESTIONS_COUNT
        and all(isinstance(q, int) and 0 <= q < len(GAMES) for q in questions)
    )


def valid_answers(answers, count: int = QUESTIONS_COUNT) -> bool:
    return (
        isinstance(answers, str)
        and len(answers) == count
        and set(answers) <= {"a", "b"}
    )


def questions_json(questions: list[int]) -> list[dict]:
    return [{"a": GAMES[i]["a"], "b": GAMES[i]["b"]} for i in questions]


def compare(one: str, two: str) -> tuple[int, int]:
    """(совпадений, процент)."""
    matches = sum(a == b for a, b in zip(one, two))
    return matches, round(matches * 100 / len(one))
