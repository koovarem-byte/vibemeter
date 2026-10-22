import json
import random

from database import (
    create_game,
    get_game,
    get_game_answers,
    add_game_answer,
    finish_game,
)


# Общая очередь поиска пары для бота и Mini App:
# user_id -> (время входа, откуда пришёл: "bot" или "app")
game_queue: dict[int, tuple[float, str]] = {}

GAMES = [
    {
        "question": "Что выберешь?",
        "a": "🌊 Жить у моря",
        "b": "🏔️ Жить в горах",
    },
    {
        "question": "Что выберешь?",
        "a": "🌙 Никогда не спать ночью",
        "b": "☀️ Никогда не спать днём",
    },
    {
        "question": "Что выберешь?",
        "a": "🎮 Всегда играть",
        "b": "🏀 Всегда заниматься спортом",
    },
    {
        "question": "Что выберешь?",
        "a": "✈️ Путешествовать каждый месяц",
        "b": "🏠 Жить в одном месте, но очень комфортно",
    },
    {
        "question": "Что выберешь?",
        "a": "💰 Много денег",
        "b": "⏳ Много свободного времени",
    },
    {
        "question": "Что выберешь?",
        "a": "📱 Неделю без телефона",
        "b": "🎧 Неделю без музыки",
    },
    {
        "question": "Что выберешь?",
        "a": "🍕 Только любимая еда",
        "b": "🍔 Каждый день новая еда",
    },
    {
        "question": "Что выберешь?",
        "a": "🎬 Смотреть фильмы",
        "b": "🎮 Играть в игры",
    },
    {
        "question": "Что выберешь?",
        "a": "🧠 Всегда знать ответ",
        "b": "🎲 Всегда рисковать",
    },
    {
        "question": "Что выберешь?",
        "a": "👥 Большая компания",
        "b": "🤝 Несколько близких друзей",
    },
]


def get_five_questions():
    return random.sample(GAMES, 5)


async def start_game(user_one: int, user_two: int):
    questions = get_five_questions()

    game_id = await create_game(
        user_one,
        user_two,
        json.dumps(
            questions,
            ensure_ascii=False,
        ),
    )

    return {
        "id": game_id,
        "user_one": user_one,
        "user_two": user_two,
        "questions": questions,
    }


def is_player(game, user_id: int) -> bool:
    return user_id in (game["user_one"], game["user_two"])


async def get_current_question(game_id: int, user_id: int):
    game = await get_game(game_id)

    if not game or not is_player(game, user_id):
        return None

    answers = await get_game_answers(
        game_id,
        user_id,
    )

    index = len(answers)

    questions = json.loads(
        game["questions_json"]
    )

    if index >= 5:
        return None

    question = questions[index].copy()
    question["index"] = index

    return question


async def save_answer(
    game_id: int,
    user_id: int,
    question_index: int,
    answer: str,
):
    if answer not in ("a", "b"):
        return False

    game = await get_game(game_id)

    if (
        not game
        or not is_player(game, user_id)
        or game["status"] == "finished"
    ):
        return False

    answers = await get_game_answers(
        game_id,
        user_id,
    )

    if len(answers) != question_index:
        return False

    return await add_game_answer(
        game_id,
        user_id,
        question_index,
        answer,
    )


async def get_progress(
    game_id: int,
    user_id: int,
):
    answers = await get_game_answers(
        game_id,
        user_id,
    )

    return len(answers)


async def calculate_result(game_id: int):
    game = await get_game(game_id)

    if not game:
        return None

    answers_one = await get_game_answers(
        game_id,
        game["user_one"],
    )

    answers_two = await get_game_answers(
        game_id,
        game["user_two"],
    )

    if len(answers_one) < 5 or len(answers_two) < 5:
        return None

    first = {
        x["question_index"]: x["answer"]
        for x in answers_one
    }

    second = {
        x["question_index"]: x["answer"]
        for x in answers_two
    }

    matches = 0

    for i in range(5):
        if first.get(i) == second.get(i):
            matches += 1

    return {
        "game_id": game_id,
        "user_one": game["user_one"],
        "user_two": game["user_two"],
        "matches": matches,
        "total": 5,
        "percentage": matches * 20,
    }


async def complete_game(game_id: int):
    result = await calculate_result(game_id)

    if not result:
        return None

    game = await get_game(game_id)

    if not game or game["status"] == "finished":
        return None

    await finish_game(game_id)

    return result

