import logging

from aiogram import Bot

import moderation
import ui

from database import (
    add_question,
    add_question_strike,
    get_question,
    get_user,
    answer_question,
    is_blocked,
    set_banned,
)
from keyboards import question_answer_keyboard

# мат и оскорбления: 1-й и 2-й раз не пропускаем с предупреждением, 3-й — бан
STRIKES_TO_BAN = 3


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

    if await is_blocked(to_user, from_user) or await is_blocked(from_user, to_user):
        return None

    question_id = await add_question(
        from_user=from_user,
        to_user=to_user,
        text=question_text,
    )

    try:
        await bot.send_message(
            to_user,
            await question_message(from_user, to_user, question_text),
            reply_markup=question_answer_keyboard(question_id),
        )
    except Exception:
        # Если отправить сообщение не удалось,
        # вопрос остаётся в базе, но возвращаем None.
        return None

    return question_id


async def question_message(from_user: int, to_user: int, text: str) -> str:
    """Вопрос + анкета автора без имени и фото: понятно, кто примерно спрашивает."""
    from handlers import calculate_vibe  # handlers импортирует этот модуль

    asker = await get_user(from_user)
    me = await get_user(to_user)
    if not asker or not asker.get("age") or not me:
        return ui.incoming_question(text)
    vibe, common = calculate_vibe(me, asker)
    return ui.incoming_question(text, asker, vibe, common)


async def check_text(bot: Bot, user_id: int, text: str) -> str | None:
    """None — текст чистый. Иначе текст ответа автору (и страйк, на 3-м бан)."""
    if not moderation.is_bad(text):
        return None
    strikes = await add_question_strike(user_id)
    if strikes < STRIKES_TO_BAN:
        return ui.BAD_WORDS_LAST if strikes == STRIKES_TO_BAN - 1 else ui.BAD_WORDS
    await set_banned(user_id, True)
    try:
        import admin
        person = await get_user(user_id)
        await admin.send_card(
            bot, person,
            note=f"🤬 <b>Автобан</b>: {strikes}-й вопрос/ответ с матом — «{ui.esc(text[:200])}»",
        )
    except Exception:
        logging.exception("Не удалось отправить автобан админу %s", user_id)
    return ui.BANNED_WORDS


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
            ui.question_answered(question["text"], answer_text),
        )
    except Exception:
        pass

    return True