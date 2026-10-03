import asyncio

from aiogram import Bot

from database import (
    add_question,
    get_question,
    answer_question,
)


# =========================================================
# ВОПРОСЫ
# =========================================================

QUESTIONS = [
    "Какую музыку можешь слушать часами?",
    "Какая игра тебе никогда не надоест?",
    "Какой фильм можешь пересматривать много раз?",
    "Чем обычно занимаешься в свободное время?",
    "Какой у тебя самый странный интерес?",
    "Что тебе реально нравится делать?",
    "Куда бы ты поехал прямо сейчас?",
    "Какой навык хотел бы освоить?",
    "Что тебя может рассмешить почти всегда?",
    "Какой у тебя идеальный выходной?",
    "Что ты выберешь: море или горы?",
    "Какой предмет тебе реально нравился в школе?",
]


def get_random_question() -> str:
    import random

    return random.choice(QUESTIONS)


# =========================================================
# СОЗДАТЬ ВОПРОС
# =========================================================

async def send_question(
    bot: Bot,
    from_user: int,
    to_user: int,
):
    question = get_random_question()

    question_id = await add_question(
        from_user=from_user,
        to_user=to_user,
        text=question,
    )

    try:
        await bot.send_message(
            to_user,
            f"""
<b>💬 Тебе задали вопрос</b>

{question}

Напиши ответ прямо сюда 👇
""",
        )

        return question_id

    except Exception:
        return None


# =========================================================
# ПОЛУЧИТЬ ВОПРОС
# =========================================================

async def get_question_data(question_id: int):
    return await get_question(question_id)


# =========================================================
# ОТВЕТИТЬ НА ВОПРОС
# =========================================================

async def submit_answer(
    bot: Bot,
    question_id: int,
    answer: str,
):
    question = await get_question(question_id)

    if not question:
        return False

    if question["answered"]:
        return False

    answer = answer.strip()

    if not answer:
        return False

    if len(answer) > 500:
        answer = answer[:500]

    await answer_question(
        question_id=question_id,
        answer=answer,
    )

    try:
        await bot.send_message(
            question["from_user"],
            f"""
<b>💬 На твой вопрос ответили</b>

<b>Вопрос:</b>
{question["text"]}

<b>Ответ:</b>
{answer}
""",
        )
    except Exception:
        pass