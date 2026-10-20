from html import escape

from aiogram import Bot

from database import (
    add_question,
    get_question,
    answer_question,
)
from keyboards import question_answer_keyboard


MAX_QUESTION_LENGTH = 500
MAX_ANSWER_LENGTH = 500


# =========================================================
# СОЗДАТЬ И ОТПРАВИТЬ ВОПРОС, НАПИСАННЫЙ ПОЛЬЗОВАТЕЛЕМ
# =========================================================

async def send_question(
    bot: Bot,
    from_user: int,
    to_user: int,
    text: str,
):
    question_text = (text or "").strip()

    if not question_text:
        return None

    if len(question_text) > MAX_QUESTION_LENGTH:
        question_text = question_text[:MAX_QUESTION_LENGTH]

    if from_user == to_user:
        return None

    question_id = await add_question(
        from_user=from_user,
        to_user=to_user,
        text=question_text,
    )

    try:
        await bot.send_message(
            to_user,
            "<b>💬 Тебе задали вопрос!</b>\n\n"
            f"{escape(question_text)}\n\n"
            "Нажми «Ответить», чтобы ответить 👇",
            reply_markup=question_answer_keyboard(question_id),
        )
    except Exception:
        # Если отправить сообщение не удалось,
        # вопрос остаётся в базе, но возвращаем None.
        return None

    return question_id


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
    user_id: int,
):
    question = await get_question(question_id)

    # Отвечать может только тот, кому задали вопрос
    if not question or question["to_user"] != user_id:
        return False

    if question["answered"]:
        return False

    answer_text = (answer or "").strip()

    if not answer_text:
        return False

    if len(answer_text) > MAX_ANSWER_LENGTH:
        answer_text = answer_text[:MAX_ANSWER_LENGTH]

    await answer_question(
        question_id=question_id,
        answer=answer_text,
    )

    try:
        await bot.send_message(
            question["from_user"],
            "<b>💬 На твой вопрос ответили!</b>\n\n"
            f"<b>Вопрос:</b>\n{escape(question['text'])}\n\n"
            f"<b>Ответ:</b>\n{escape(answer_text)}",
        )
    except Exception:
        pass

    return True