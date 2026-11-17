"""Тренажёр переписки «Шах и чат» (ТЗ 16.11).

Режимы: партия с ИИ-девушкой (/play), задача дня (/daily), разбор переписки (/razbor),
база ходов (/baza), вопрос автору (/ask), рейтинг (/me), лидеры (/top), помощь (/help).
Роутер подключается в bot.py раньше старого handlers.router.
Без ANTHROPIC_API_KEY партии и задача дня идут на быстрых задачах с вариантами.
"""

import html
import logging
import os
import random
import re

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import baza
import facts
import llm
import puzzles
import situations
import ui
from config import ADMIN_ID
from database import (
    active_chat_game,
    add_author_question,
    chat_me,
    chat_place,
    chat_top,
    create_chat_game,
    daily_better_than,
    finish_chat_game,
    games_today,
    get_chat_daily,
    get_user,
    log_event,
    log_razbor,
    razbors_today,
    save_chat_daily,
    save_chat_history,
    take_author_question,
)
from keyboards import (
    after_game_keyboard,
    ask_keyboard,
    baza_back_keyboard,
    baza_keyboard,
    fact_keyboard,
    friend_keyboard,
    main_menu,
    situations_keyboard,
)
from states import TrainState

router = Router()

GAMES_PER_DAY = int(os.getenv("GAMES_PER_DAY", "5"))
RAZBOR_PER_DAY = int(os.getenv("RAZBOR_PER_DAY", "1"))
MAX_MOVES = 5           # ходов игрока в партии (ТЗ: 3–5)
MAX_MOVE_LEN = 400      # длиннее — это не переписка

# сообщения о желании навредить себе: выходим из игры, отвечаем по-человечески, дублируем админу
CRISIS = re.compile(
    r"(убить себя|убью себя|покончить с собой|покончу с собой|суицид|самоубий|не хочу жить|"
    r"хочу умереть|вскрыть вены|вскрою вены|наложить на себя руки|свести сч[её]ты с жизнью|"
    r"порезать себя|режу себя)",
    re.IGNORECASE,
)


async def _crisis(message: Message, state: FSMContext) -> bool:
    text = message.text or message.caption or ""
    if not CRISIS.search(text):
        return False
    await state.clear()
    game = await active_chat_game(message.from_user.id)
    if game:
        await finish_abandoned(game)
    await message.answer(ui.CRISIS_TEXT, reply_markup=main_menu())
    try:
        user = message.from_user
        await message.bot.send_message(
            ADMIN_ID,
            f"🆘 <b>Тревожное сообщение</b> от {html.escape(user.full_name)} (/u_{user.id}):\n\n"
            f"<i>{html.escape(text[:500])}</i>",
        )
    except Exception:
        logging.exception("Не удалось переслать тревожное сообщение админу")
    await log_event(message.from_user.id, "crisis")
    return True


async def finish_abandoned(game):
    from database import get_pool
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute("UPDATE chat_games SET status = 'abandoned' WHERE id = $1", game["id"])


async def _registered(message: Message) -> bool:
    if await get_user(message.from_user.id):
        return True
    await message.answer(ui.NEED_START)
    return False


async def _typing(message: Message):
    try:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    except Exception:
        pass


# =========================================================
# ПАРТИЯ
# =========================================================

async def open_play_menu(message: Message, user_id: int, state: FSMContext):
    await state.clear()
    if not llm.available():
        import handlers
        await message.answer(ui.LLM_SOON, reply_markup=main_menu())
        await handlers.show_puzzle(message, user_id)
        return
    await message.answer(ui.PLAY_CHOOSE, reply_markup=situations_keyboard(await situations.all_situations()))


@router.message(F.text.in_(ui.menu_texts(ui.MENU_PLAY)))
@router.message(Command("play", "chess"))
async def play_cmd(message: Message, state: FSMContext):
    if await _registered(message):
        await open_play_menu(message, message.from_user.id, state)


@router.callback_query(F.data == "play_menu")
async def play_menu_cb(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await open_play_menu(callback.message, callback.from_user.id, state)


@router.callback_query(F.data.startswith("play:"))
async def play_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    key = callback.data.split(":", 1)[1]
    items = await situations.all_situations()
    sit = random.choice(items) if key == "random" else next((s for s in items if s["key"] == key), None)
    if not sit:
        await callback.answer("Такой партии нет", show_alert=True)
        return
    if user_id != ADMIN_ID and await games_today(user_id) >= GAMES_PER_DAY:
        await callback.answer()
        await callback.message.answer(ui.PLAY_LIMIT, reply_markup=after_game_keyboard())
        return
    await callback.answer()
    history = [{"who": "her", "text": sit["opening"]}] if sit.get("opening") else []
    game_id = await create_chat_game(user_id, sit["key"], sit["difficulty"], history)
    await state.set_state(TrainState.playing)
    await state.update_data(game_id=game_id)
    await callback.message.answer(ui.game_intro(sit))
    await log_event(user_id, "game_start", sit["key"])


@router.message(TrainState.playing, F.text)
async def play_move(message: Message, state: FSMContext):
    if await _crisis(message, state):
        return
    move = message.text.strip()
    if len(move) > MAX_MOVE_LEN:
        await message.answer(ui.TOO_LONG)
        return
    game = await active_chat_game(message.from_user.id)
    if not game:
        await state.clear()
        await message.answer(ui.GAME_NONE, reply_markup=main_menu())
        return
    sit = await situations.get(game["situation"])
    if not sit:
        await state.clear()
        await message.answer(ui.GAME_NONE, reply_markup=main_menu())
        return

    history = game["history"]
    await _typing(message)
    verdict = await llm.judge(sit, history, move)
    history.append({"who": "me", "text": move, "badge": verdict["badge"], "eval": verdict["eval"],
                    "coach": verdict["coach"], "best": verdict.get("best_move") or ""})
    await message.answer(ui.move_verdict(verdict))

    my_moves = [m for m in history if m["who"] == "me"]
    finished = verdict["finished"] or len(my_moves) >= MAX_MOVES
    if not finished:
        await _typing(message)
        try:
            reply = await llm.girl(sit, history, verdict)
        except llm.LLMError:
            await save_chat_history(game["id"], history)
            await message.answer(ui.LLM_BUSY)
            return
        history.append({"who": "her", "text": reply})
        await message.answer(ui.her_line(reply))
        if "всё, пока" in reply.lower() or "все, пока" in reply.lower():
            finished = True
            verdict = {**verdict, "result": "mate"}
    if not finished:
        await save_chat_history(game["id"], history)
        return
    await end_game(message, state, game, sit, history, verdict)


async def end_game(message: Message, state: FSMContext, game, sit, history, last_verdict):
    my_moves = [m for m in history if m["who"] == "me"]
    avg = sum(m["eval"] for m in my_moves) / len(my_moves)
    result = last_verdict.get("result")
    if result not in ("mate", "stalemate", "win"):
        result = "win" if avg >= 3 else ("mate" if avg <= -3 else "stalemate")
    user = await get_user(message.chat.id)
    before = user["chess_rating"]
    import rating
    from database import rated_count
    after = rating.update(before, max(0, game["difficulty"] - 1000),
                          rating.game_score([m.get("badge") for m in my_moves]), await rated_count(message.chat.id))
    # лучший ход — подсказка судьи к самому слабому ходу партии
    worst = min(my_moves, key=lambda m: m["eval"])
    best = worst.get("best") if worst["badge"] not in ("!!", "#") else None
    await finish_chat_game(game["id"], message.chat.id, history, result, avg, before, after, best)
    await state.clear()
    await message.answer(
        ui.game_result(result, before, after, puzzles.rank(after), best, avg),
        reply_markup=after_game_keyboard(),
    )
    await log_event(message.chat.id, "game_end", f"{sit['key']}:{result}")


@router.message(TrainState.playing)
async def play_not_text(message: Message):
    await message.answer(ui.TEXT_ONLY)


# =========================================================
# ЗАДАЧА ДНЯ
# =========================================================

async def open_daily(message: Message, user_id: int, state: FSMContext):
    await state.clear()
    if not llm.available():
        import handlers
        await handlers.show_puzzle(message, user_id)
        return
    done = await get_chat_daily(user_id)
    if done:
        better, total = await daily_better_than(done["eval"])
        v = {"badge": done["badge"], "eval": done["eval"], "coach": done["coach"] or "", "best_move": ""}
        await message.answer(ui.daily_result(v, better, total, already=True), reply_markup=after_game_keyboard())
        return
    sit = await situations.daily()
    await state.set_state(TrainState.daily)
    await message.answer(ui.DAILY_ASK.format(context=html.escape(sit["context"]), opening=html.escape(sit["opening"])))


@router.message(F.text.in_(ui.menu_texts(ui.MENU_DAILY)))
@router.message(Command("daily"))
async def daily_cmd(message: Message, state: FSMContext):
    if await _registered(message):
        await open_daily(message, message.from_user.id, state)


@router.callback_query(F.data == "daily")
async def daily_cb(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await open_daily(callback.message, callback.from_user.id, state)


@router.message(TrainState.daily, F.text)
async def daily_move(message: Message, state: FSMContext):
    if await _crisis(message, state):
        return
    move = message.text.strip()
    if len(move) > MAX_MOVE_LEN:
        await message.answer(ui.TOO_LONG)
        return
    sit = await situations.daily()
    await _typing(message)
    verdict = await llm.judge(sit, [{"who": "her", "text": sit["opening"]}], move)
    await state.clear()
    if not await save_chat_daily(message.from_user.id, sit["key"], move, verdict["badge"],
                                 verdict["eval"], verdict["coach"]):
        await open_daily(message, message.from_user.id, state)
        return
    better, total = await daily_better_than(verdict["eval"])
    await message.answer(ui.daily_result(verdict, better, total), reply_markup=after_game_keyboard())
    await log_event(message.from_user.id, "daily_done", f"{verdict['badge']}")


# =========================================================
# РАЗБОР ПЕРЕПИСКИ
# =========================================================

@router.message(F.text.in_(ui.menu_texts(ui.MENU_RAZBOR)))
@router.message(Command("razbor"))
async def razbor_cmd(message: Message, state: FSMContext):
    if not await _registered(message):
        return
    await state.clear()
    if not llm.available():
        await message.answer(ui.RAZBOR_SOON, reply_markup=main_menu())
        return
    if message.from_user.id != ADMIN_ID and await razbors_today(message.from_user.id) >= RAZBOR_PER_DAY:
        await message.answer(ui.RAZBOR_LIMIT, reply_markup=main_menu())
        return
    await state.set_state(TrainState.razbor)
    await message.answer(ui.RAZBOR_ASK)


@router.message(TrainState.razbor, F.photo | F.text)
async def razbor_input(message: Message, state: FSMContext):
    if await _crisis(message, state):
        return
    await state.clear()
    await message.answer(ui.RAZBOR_WAIT)
    await _typing(message)
    try:
        if message.photo:
            # картинку держим только в памяти на время разбора и нигде не сохраняем
            buf = await message.bot.download(message.photo[-1])
            text = await llm.razbor(message.caption or "", image=buf.read())
            buf.close()
        else:
            text = await llm.razbor("", text=message.text)
    except llm.LLMError:
        await message.answer(ui.LLM_BUSY, reply_markup=main_menu())
        return
    await log_razbor(message.from_user.id)
    await message.answer(html.escape(text)[:4000], reply_markup=after_game_keyboard())
    await log_event(message.from_user.id, "razbor_done")


@router.message(TrainState.razbor)
async def razbor_wrong(message: Message):
    await message.answer(ui.RAZBOR_ASK)


# =========================================================
# БАЗА ХОДОВ
# =========================================================

@router.message(F.text.in_(ui.menu_texts(ui.MENU_BAZA)))
@router.message(Command("baza"))
async def baza_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(ui.BAZA_CHOOSE, reply_markup=baza_keyboard(baza.BAZA))


@router.callback_query(F.data == "baza_menu")
async def baza_menu_cb(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(ui.BAZA_CHOOSE, reply_markup=baza_keyboard(baza.BAZA))


@router.callback_query(F.data.startswith("baza:"))
async def baza_item(callback: CallbackQuery):
    item = baza.BAZA.get(callback.data.split(":", 1)[1])
    await callback.answer()
    if item:
        await callback.message.answer(ui.baza_card(item), reply_markup=baza_back_keyboard())


# =========================================================
# ВОПРОС АВТОРУ
# =========================================================

@router.message(F.text.in_(ui.menu_texts(ui.MENU_ASK)))
@router.message(Command("ask"))
async def ask_cmd(message: Message, state: FSMContext):
    if not await _registered(message):
        return
    await state.set_state(TrainState.ask)
    await message.answer(ui.ASK_PROMPT)


async def _forward_to_author(bot, user, qid: int, question: str):
    await bot.send_message(
        ADMIN_ID,
        f"✍️ <b>Вопрос автору</b> №{qid} от {html.escape(user.full_name)} (/u_{user.id}):\n\n"
        f"{html.escape(question[:3000])}\n\n<i>Ответить: /reply {user.id} текст</i>",
    )


@router.message(TrainState.ask, F.text)
async def ask_input(message: Message, state: FSMContext):
    if await _crisis(message, state):
        return
    await state.clear()
    question = message.text.strip()[:3000]
    if not llm.available():
        qid = await add_author_question(message.from_user.id, question, None)
        await take_author_question(qid, message.from_user.id)
        await _forward_to_author(message.bot, message.from_user, qid, question)
        await message.answer(ui.ASK_FORWARDED_NO_LLM, reply_markup=main_menu())
        await log_event(message.from_user.id, "ask_sent", "forwarded")
        return
    await _typing(message)
    try:
        answer = await llm.ask(question)
    except llm.LLMError:
        answer = None
    qid = await add_author_question(message.from_user.id, question, answer)
    await message.answer(html.escape(answer) if answer else ui.LLM_BUSY, reply_markup=ask_keyboard(qid))
    await log_event(message.from_user.id, "ask_sent")


@router.callback_query(F.data.startswith("ask_fwd:"))
async def ask_forward(callback: CallbackQuery):
    qid = int(callback.data.split(":")[1])
    question = await take_author_question(qid, callback.from_user.id)
    if not question:
        await callback.answer(ui.ASK_ALREADY, show_alert=True)
        return
    await _forward_to_author(callback.bot, callback.from_user, qid, question)
    await callback.answer(ui.ASK_SENT, show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


# =========================================================
# РЕЙТИНГ, ЛИДЕРЫ, ПОМОЩЬ, ФАКТ, ДРУГ
# =========================================================

@router.message(F.text.in_(ui.menu_texts(ui.MENU_ME)))
@router.message(Command("me"))
async def me_cmd(message: Message, state: FSMContext):
    if not await _registered(message):
        return
    await state.clear()
    user = await get_user(message.from_user.id)
    me = await chat_me(message.from_user.id)
    place, total = await chat_place(message.from_user.id)
    best = None
    if me["best_situation"]:
        sit = await situations.get(me["best_situation"])
        best = f"{(sit or {}).get('title', me['best_situation'])} ({me['best_avg']:+.1f})"
    rating = user["chess_rating"]
    await message.answer(ui.trainer_me(
        rating, puzzles.rank(rating), user["streak_days"], me["games"], me["wins"], best,
        place, total, puzzles.next_rank(rating),
    ), reply_markup=after_game_keyboard())


@router.message(F.text.in_(ui.menu_texts(ui.MENU_TOP)))
@router.message(Command("top"))
async def top_cmd(message: Message, state: FSMContext):
    if not await _registered(message):
        return
    await state.clear()
    user = await get_user(message.from_user.id)
    place, total = await chat_place(message.from_user.id)
    await message.answer(ui.trainer_top(await chat_top(20), place, total, user["chess_rating"]),
                         reply_markup=after_game_keyboard())


@router.callback_query(F.data == "pz_top")
async def top_cb(callback: CallbackQuery):
    await callback.answer()
    user = await get_user(callback.from_user.id)
    place, total = await chat_place(callback.from_user.id)
    await callback.message.answer(
        ui.trainer_top(await chat_top(20), place, total, (user or {}).get("chess_rating") or 0),
        reply_markup=after_game_keyboard())


@router.message(Command("help"))
async def help_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(ui.HELP_TEXT, reply_markup=main_menu())


@router.message(F.text.in_(ui.menu_texts(ui.MENU_FACT)))
@router.message(Command("fact"))
async def fact_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(ui.fact_of_day(facts.render(facts.fact_of_day())), reply_markup=fact_keyboard())


@router.message(F.text.in_(ui.menu_texts(ui.MENU_FRIEND)))
async def friend_cmd(message: Message, state: FSMContext):
    await state.clear()
    link = f"https://t.me/{(await message.bot.me()).username}?start=pz_{puzzles.today_index()}"
    await message.answer(ui.friend_invite(link), reply_markup=friend_keyboard(link))


# =========================================================
# АДМИН: ответ на вопрос
# =========================================================

@router.message(Command("reply"), F.from_user.id == ADMIN_ID)
async def admin_reply(message: Message):
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("Формат: /reply ID текст")
        return
    try:
        await message.bot.send_message(int(parts[1]), f"✍️ <b>Ответ автора</b>\n\n{html.escape(parts[2])}")
        await message.answer("Отправил 👌")
    except Exception:
        await message.answer("Не доставилось: человек заблокировал бота или не начинал диалог")
