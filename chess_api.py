"""Mini App «Шах и чат»: страница /play/ и API /play/api/*.

Каждый запрос к API несёт заголовок X-Init-Data (Telegram.WebApp.initData), проверяем подпись.
Анкета не нужна: достаточно, чтобы человек нажал /start в боте (есть строка в users).
Старый Mini App знакомств (/app/) не трогаем.
"""

import html
import logging
import os
import re
import time
import unicodedata
from pathlib import Path

from aiohttp import web
from aiogram.utils.web_app import safe_parse_webapp_init_data

import facts
import learn
import partii
import puzzles
import rating
from config import ADMIN_ID, BOT_TOKEN
from database import (
    app_game_finish,
    app_game_get,
    app_game_move,
    app_game_start,
    app_games_finished,
    app_games_summary,
    beta_add_feedback,
    beta_has_feedback,
    beta_is_tester,
    beta_join,
    rated_count,
    set_level,
    chat_place,
    chess_period_top,
    chess_profile,
    get_user,
    learn_answer,
    learn_open,
    learn_state,
    log_event,
    mark_seen,
    touch_user,
    solve_puzzle,
    solved_puzzles,
)

PLAY_DIR = Path(__file__).parent / "webapp_chess"
INIT_DATA_TTL = 24 * 60 * 60
PERIODS = {"day": 1, "week": 7, "all": None}

# Закрытый бета-тест (17.11): Mini App только для первых BETA_SLOTS человек.
# Релиз: BETA_SLOTS=0 в переменных Bothost — открыто всем.
BETA_SLOTS = int(os.getenv("BETA_SLOTS", "30"))


async def load_slots():
    """Число мест можно менять без пересборки: /beta_slots N (app_state.beta_slots)."""
    global BETA_SLOTS
    from database import get_app_state
    v = await get_app_state("beta_slots")
    if v is not None and v.lstrip("-").isdigit():
        BETA_SLOTS = int(v)
# после стольких партий без отзыва дальше не пускаем — сначала мнение
FEEDBACK_AFTER_GAMES = 2
OPEN_FOR_ALL = ("/play/api/state", "/play/api/beta/join")


# 19.11 (отзыв #40): отзыв из невидимых символов прошёл проверку длины.
# Вырезаем «форматные» символы (zero-width, U+2060…, BOM, мягкий перенос) и пустые
# буквы-заполнители (хангыль), пробелы схлопываем; нужно хотя бы MIN_LETTERS букв.
FILLERS = "\u115f\u1160\u3164\uffa0\u2800"
MIN_LETTERS = 5


def clean_text(text: str) -> str:
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf" and ch not in FILLERS)
    return re.sub(r"\s+", " ", text).strip()


def letters(text: str) -> int:
    return sum(ch.isalpha() for ch in text)


def error(code: str, status: int):
    return web.json_response({"error": code}, status=status)


@web.middleware
async def play_auth(request, handler):
    if not request.path.startswith("/play/api/"):
        response = await handler(request)
        if request.path.startswith("/play"):
            response.headers["Cache-Control"] = "no-cache"
        return response
    try:
        data = safe_parse_webapp_init_data(BOT_TOKEN, request.headers.get("X-Init-Data", ""))
    except ValueError:
        return error("bad_init_data", 401)
    if not data.user or time.time() - data.auth_date.timestamp() > INIT_DATA_TTL:
        return error("bad_init_data", 401)
    user = await get_user(data.user.id)
    if not user:
        return error("no_user", 404)
    if user["is_banned"]:
        return error("banned", 403)
    uid = user["telegram_id"]
    request["tester"] = BETA_SLOTS <= 0 or uid == ADMIN_ID or await beta_is_tester(uid)
    if not request["tester"] and request.path not in OPEN_FOR_ALL:
        return error("beta_closed", 403)
    # задача, партия и состояние считаются заходом: серия дней и last_active, как в боте
    if request.path in ("/play/api/state", "/play/api/move", "/play/api/partiya/move", "/play/api/learn/quiz"):
        await touch_user(user["telegram_id"])
        user = await get_user(user["telegram_id"]) or user
    else:
        await mark_seen(user["telegram_id"])
    request["user"] = user
    return await handler(request)


def first_name(name: str | None) -> str:
    return ((name or "").strip().split() or ["Игрок"])[0][:20]


def me_json(user, done: set[int]) -> dict:
    """done — решённые задачи; «из скольких» считаем по задачам своего уровня (19.11)."""
    level = puzzles.user_level(user)
    pool = puzzles.pool(level)
    r = user["chess_rating"] or 0
    nxt = puzzles.next_rank(r)
    prev = max([limit for limit, _ in puzzles.RANKS if limit <= r] or [0])
    return {
        "name": first_name(user["full_name"]),
        "rating": r,
        "rank": puzzles.rank(r),
        "rank_from": prev,
        "next": {"at": nxt[0], "rank": nxt[1]} if nxt else None,
        "streak": user["streak_days"] or 0,
        "best_streak": max(user.get("best_streak") or 0, user["streak_days"] or 0),
        "solved": len(done & set(pool)),
        "total": len(pool),
        "level": level,
        "knowledge": user.get("learn_points") or 0,
    }


def puzzle_json(pid: int, number: int, level: str) -> dict:
    p = puzzles.PUZZLES[pid]
    return {
        "id": pid,
        "number": number,
        "daily": pid == puzzles.today_index(level),
        "chat": p["chat"],
        "moves": [{"idx": i, "text": p["moves"][i][0]} for i in puzzles.move_order(pid)],
    }


def next_puzzle(done: set[int], level: str):
    return next((pid for pid in puzzles.pool(level) if pid not in done), None)


def puzzles_json(user, done: set[int]) -> dict:
    """Следующая задача, задача дня и «я» — по уровню игрока."""
    level = puzzles.user_level(user)
    pid = next_puzzle(done, level)
    me = me_json(user, done)
    return {
        "me": me,
        "puzzle": puzzle_json(pid, me["solved"] + 1, level) if pid is not None else None,
        "daily_done": puzzles.today_index(level) in done,
    }


async def api_state(request):
    user = request["user"]
    done = await solved_puzzles(user["telegram_id"])
    return web.json_response({
        **puzzles_json(user, done),
        "bot": (await request.app["bot"].me()).username,
        "beta": await beta_json(request),
    })


async def beta_json(request) -> dict:
    uid = request["user"]["telegram_id"]
    return {
        "on": BETA_SLOTS > 0,
        "tester": request["tester"],
        "slots": BETA_SLOTS,
        "feedback": await beta_has_feedback(uid),
        "games": await app_games_finished(uid),
        "need_feedback": await need_feedback(uid),
    }


async def need_feedback(uid: int) -> bool:
    return (BETA_SLOTS > 0 and uid != ADMIN_ID and not await beta_has_feedback(uid)
            and await app_games_finished(uid) >= FEEDBACK_AFTER_GAMES)


async def api_beta_join(request):
    uid = request["user"]["telegram_id"]
    if request["tester"]:
        return web.json_response({"ok": True})
    ok, num, total = await beta_join(uid, BETA_SLOTS)
    await log_event(uid, "beta_join" if ok else "beta_wait", str(num))
    return web.json_response({"ok": ok, "num": num, "total": total, "slots": BETA_SLOTS})


async def api_feedback(request):
    user = request["user"]
    try:
        body = await request.json()
        text = clean_text(str(body.get("text") or ""))[:2000]
        stars = body.get("stars")
        stars = int(stars) if stars is not None else None
        if stars is not None and not 1 <= stars <= 5:
            raise ValueError
    except (ValueError, TypeError):
        return error("bad_request", 400)
    if letters(text) < MIN_LETTERS:
        return error("too_short", 400)
    fid = await beta_add_feedback(user["telegram_id"], stars, text)
    try:
        who = f"@{user['username']}" if user.get("username") else html.escape(first_name(user["full_name"]))
        await request.app["bot"].send_message(
            ADMIN_ID,
            f"📝 Отзыв бета-теста #{fid} от {who} (<code>{user['telegram_id']}</code>)\n"
            f"{'⭐' * (stars or 0)}\n\n{html.escape(text)}",
        )
    except Exception:
        logging.warning("Отзыв %s не отправился админу", fid)
    return web.json_response({"ok": True})


async def api_move(request):
    user = request["user"]
    try:
        body = await request.json()
        pid, idx = int(body["id"]), int(body["idx"])
        puzzle = puzzles.PUZZLES[pid]
        move, mark, why = puzzle["moves"][idx]
    except (ValueError, KeyError, TypeError, IndexError):
        return error("bad_request", 400)
    before = user["chess_rating"] or 0
    elo = rating.update(before, puzzle.get("rating", rating.PUZZLE_RATING), rating.SCORE[mark],
                        await rated_count(user["telegram_id"]), blitz=True)
    res = await solve_puzzle(user["telegram_id"], pid, mark, elo - before)
    if res is None:
        return error("already_solved", 409)
    new_rating, rated = res
    await log_event(user["telegram_id"], "puzzle_app", f"{pid}:{mark}")
    best = max(puzzle["moves"], key=lambda m: puzzles.DELTA[m[1]])
    done = await solved_puzzles(user["telegram_id"])
    fresh = {**user, "chess_rating": new_rating}
    nxt = puzzles_json(fresh, done)
    return web.json_response({
        "mark": mark,
        "name": rating.NAMES[mark],
        "why": why,
        "best": best[0] if best[1] != mark else None,
        "others": [{"text": t, "mark": m, "why": w} for t, m, w in puzzle["moves"] if t != move],
        "delta": new_rating - before,
        "rated": rated,
        "rank_up": puzzles.rank(new_rating) != puzzles.rank(before),
        "me": nxt["me"],
        "puzzle": nxt["puzzle"],
    })


async def api_top(request):
    user = request["user"]
    period = request.query.get("period", "all")
    rows = await chess_period_top(PERIODS.get(period), 50)
    me_id = user["telegram_id"]
    items = [{
        "place": i + 1,
        "name": first_name(r["full_name"]),
        "points": r["points"],
        "rank": puzzles.rank(r["chess_rating"] or 0),
        "me": r["telegram_id"] == me_id,
    } for i, r in enumerate(rows)]
    mine = next((it for it in items if it["me"]), None)
    if mine is None and period == "all":
        place, total = await chat_place(me_id)
        mine = {"place": place, "points": user["chess_rating"] or 0, "total": total} if place else None
    owner = None
    if period == "all":
        o = await get_user(ADMIN_ID)
        if o:
            owner = {"name": first_name(o["full_name"]), "points": o["chess_rating"] or 0,
                     "rank": puzzles.rank(o["chess_rating"] or 0), "me": o["telegram_id"] == me_id}
    if me_id == ADMIN_ID:
        mine = None
    return web.json_response({"items": items, "me": mine, "owner": owner})


def fact_json(f) -> dict:
    return {"id": f["id"], "text": f["text"], "tip": f["tip"], "source": f["source"], "url": f.get("url")}


async def api_facts(request):
    day = facts.fact_of_day()
    rest = [f for f in facts.for_bot() if f["id"] != day["id"]]
    return web.json_response({"day": fact_json(day), "items": [fact_json(f) for f in rest]})


async def learn_json(uid: int) -> dict:
    st = await learn_state(uid)
    items = []
    for a in learn.today_set(st["read"], st["today"]):
        fid = a["id"]
        q = learn.QUIZ[fid]
        answered = st["quiz"].get(fid)
        items.append({
            **fact_json(a),
            "opened": fid in st["today"],
            "answered": answered is not None,
            "ok": answered,
            "question": q[0],
            "options": learn.quiz_options(fid, uid),
            "correct": q[1] if answered is not None else None,
            # награда ещё возможна: за эту статью не давали (и сегодня не ответил мимо)
            "reward": learn.REWARD if fid not in st["rewarded"] and answered is None else 0,
            "earned": fid in st["rewarded"] and answered is True,
        })
    return {"items": items, "per_day": learn.PER_DAY, "reward": learn.REWARD, "points": st["points"],
            "done": sum(1 for i in items if i["answered"]), "total_read": len(st["read"]),
            "all": len(learn.articles())}


async def api_learn(request):
    return web.json_response(await learn_json(request["user"]["telegram_id"]))


async def api_learn_open(request):
    uid = request["user"]["telegram_id"]
    fid = str((await request.json()).get("id", ""))
    st = await learn_state(uid)
    if fid not in {a["id"] for a in learn.today_set(st["read"], st["today"])}:
        return error("not_today", 400)
    await learn_open(uid, fid)
    return web.json_response({"ok": True})


async def api_learn_quiz(request):
    user = request["user"]
    uid = user["telegram_id"]
    body = await request.json()
    fid, idx = str(body.get("id", "")), body.get("idx")
    st = await learn_state(uid)
    if fid not in {a["id"] for a in learn.today_set(st["read"], st["today"])} or idx not in (0, 1, 2):
        return error("bad_quiz", 400)
    prev, earned = await learn_answer(uid, fid, idx == 0, learn.REWARD)
    ok = prev if prev is not None else idx == 0
    if prev is None:
        await log_event(uid, "learn_quiz", f"{fid}:{'ok' if ok else 'no'}")
    fresh = await get_user(uid) or user
    done = await solved_puzzles(uid)
    return web.json_response({"ok": ok, "correct": learn.QUIZ[fid][1], "delta": earned,
                              "me": me_json(fresh, done), "learn": await learn_json(uid)})


async def api_profile(request):
    user = request["user"]
    uid = user["telegram_id"]
    done = await solved_puzzles(uid)
    prof = await chess_profile(user["telegram_id"])
    place, total = await chat_place(uid)
    learning = await learn_state(uid)
    return web.json_response({
        "me": me_json(user, done), **prof, "place": place, "players": total,
        "lessons_done_today": sum(answer is not None for answer in learning["quiz"].values()),
        "lessons_goal": learn.PER_DAY,
    })


# ---------- партии без ИИ ----------

# «Блиц» (19.11, отзыв #32): 30 секунд на ход, таймер на фронте. Не успел — ход ?? и партия идёт дальше.
# Время не проверяем на сервере: рейтинг за блиц тот же, выгоды обманывать нет.
BLITZ_SECONDS = 30
TIMEOUT_MOVE = ("(долго думал)", "??", "30 секунд прошли. Пока ты думал, она ушла в другой чат",
                "ладно, мне тут пишут, потом отвечу")

def step_json(game_id: int, p: dict, step: int) -> dict:
    st = p["steps"][step]
    return {
        "n": step + 1,
        "total": len(p["steps"]),
        "her": st["her"],
        "options": [{"idx": i, "text": st["options"][i][0]} for i in partii.shown(game_id, st, step)],
    }


def partiya_meta(p: dict) -> dict:
    return {"id": p["id"], "title": p["title"], "rating": p["rating"], "intro": p["intro"], "moves": len(p["steps"]),
            "level": p["level"]}


def partii_for(level: str) -> list[dict]:
    """«Начинаю» — только партии start; «Опытный» — сначала свои, потом школьные (19.11)."""
    own = sorted((p for p in partii.PARTII if p["level"] == level), key=lambda p: p["rating"])
    rest = sorted((p for p in partii.PARTII if p["level"] != level), key=lambda p: p["rating"])
    return own + (rest if level == "pro" else [])


async def api_level(request):
    user = request["user"]
    try:
        level = str((await request.json())["level"])
    except (ValueError, KeyError, TypeError):
        return error("bad_request", 400)
    if level not in puzzles.LEVELS:
        return error("bad_request", 400)
    await set_level(user["telegram_id"], level)
    await log_event(user["telegram_id"], "level", level)
    fresh = {**user, "level": level}
    return web.json_response(puzzles_json(fresh, await solved_puzzles(user["telegram_id"])))


async def api_partii(request):
    summary = await app_games_summary(request["user"]["telegram_id"])
    items = []
    for p in partii_for(puzzles.user_level(request["user"])):
        done = summary.get(p["id"])
        items.append({**partiya_meta(p), "result": done and done["result"],
                      "accuracy": done and rating.accuracy(done["marks"])})
    return web.json_response({"items": items, "level": puzzles.user_level(request["user"]),
                              "beta": await beta_json(request)})


async def api_partiya_start(request):
    uid = request["user"]["telegram_id"]
    try:
        body = await request.json()
        p = partii.BY_ID[str(body["id"])]
        blitz = bool(body.get("blitz"))
    except (ValueError, KeyError, TypeError, AttributeError):
        return error("bad_request", 400)
    if await need_feedback(uid):
        return error("need_feedback", 403)
    g = await app_game_start(uid, p["id"], blitz)
    await log_event(uid, "partiya_start", p["id"] + (":blitz" if blitz else ""))
    return web.json_response({"game_id": g["id"], "rated": g["rated"], "blitz": blitz, "seconds": BLITZ_SECONDS,
                              "partiya": partiya_meta(p), "step": step_json(g["id"], p, 0)})


async def api_partiya_move(request):
    user = request["user"]
    uid = user["telegram_id"]
    try:
        body = await request.json()
        g = await app_game_get(int(body["game_id"]), uid)
        timeout = bool(body.get("timeout"))
        idx = -1 if timeout else int(body["idx"])
    except (ValueError, KeyError, TypeError, AttributeError):
        return error("bad_request", 400)
    if not g or g["status"] != "active":
        return error("game_over", 409)
    p = partii.BY_ID.get(g["partiya"])
    step = g["step"]
    if not p or step >= len(p["steps"]):
        return error("bad_request", 400)
    # 19.11: на ходе видны 3 варианта из пула — ходить можно только ими, разбор тоже по ним
    visible = partii.shown(g["id"], p["steps"][step], step)
    if timeout and not g.get("blitz"):
        return error("bad_request", 400)
    if not timeout and idx not in visible:
        return error("bad_request", 400)
    opts = p["steps"][step]["options"]
    opt = TIMEOUT_MOVE if timeout else opts[idx]
    text, mark, why, reply = opt[:4]
    mated = len(opt) > 4 and opt[4] == "mate"
    moves = g["moves"] + [{"step": step, "idx": idx, "mark": mark, **({"timeout": True} if timeout else {})}]
    best = max((opts[i] for i in visible), key=lambda o: rating.SCORE[o[1]])
    out = {
        "mark": mark, "name": rating.NAMES[mark], "why": why, "reply": reply,
        "best": best[0] if best[1] != mark else None,
        "others": [{"text": opts[i][0], "mark": opts[i][1], "why": opts[i][2]} for i in visible if i != idx],
    }
    last = step + 1 >= len(p["steps"])
    if not (mated or last):
        await app_game_move(g["id"], moves, step + 1)
        out["next"] = step_json(g["id"], p, step + 1)
        return web.json_response(out)
    marks = [m["mark"] for m in moves]
    review = []
    for turn, move in enumerate(moves):
        step_data = p["steps"][move["step"]]
        visible = partii.shown(g["id"], step_data, move["step"])
        options = step_data["options"]
        best_idx = max(visible, key=lambda i: rating.SCORE[options[i][1]])
        selected = TIMEOUT_MOVE if move.get("timeout") else options[move["idx"]]
        review.append({
            "turn": turn + 1,
            "her": step_data["her"],
            "move": selected[0],
            "mark": selected[1],
            "name": rating.NAMES[selected[1]],
            "why": selected[2],
            "reply": selected[3],
            "best": options[best_idx][0] if options[best_idx][1] != selected[1] else None,
            "options": [{
                "text": options[i][0],
                "mark": options[i][1],
                "name": rating.NAMES[options[i][1]],
                "why": options[i][2],
                "selected": i == move["idx"],
            } for i in visible],
        })
    result = rating.result_of(marks, mated)
    before = user["chess_rating"] or 0
    after = rating.update(before, p["rating"], rating.game_score(marks), await rated_count(uid)) if g["rated"] else before
    await app_game_finish(g["id"], uid, moves, result, before, after, g["rated"])
    await log_event(uid, "partiya_end", f"{p['id']}:{result}")
    done = await solved_puzzles(uid)
    out["final"] = {
        "result": result, "rated": g["rated"], "before": before, "after": after, "delta": after - before,
        "accuracy": rating.accuracy(marks), "marks": marks, "review": review,
        "expected": round(rating.expected(before, p["rating"]) * 100),
        "rank_up": puzzles.rank(after) != puzzles.rank(before),
        "me": me_json({**user, "chess_rating": after}, done),
        "need_feedback": await need_feedback(uid),
    }
    return web.json_response(out)


async def index(request):
    return web.FileResponse(PLAY_DIR / "index.html")


async def to_index(request):
    raise web.HTTPFound("/play/")


def setup_play(app: web.Application):
    app.middlewares.append(play_auth)
    app.router.add_get("/play/api/state", api_state)
    app.router.add_post("/play/api/move", api_move)
    app.router.add_get("/play/api/top", api_top)
    app.router.add_get("/play/api/facts", api_facts)
    app.router.add_get("/play/api/profile", api_profile)
    app.router.add_get("/play/api/learn", api_learn)
    app.router.add_post("/play/api/learn/open", api_learn_open)
    app.router.add_post("/play/api/learn/quiz", api_learn_quiz)
    app.router.add_post("/play/api/beta/join", api_beta_join)
    app.router.add_post("/play/api/feedback", api_feedback)
    app.router.add_get("/play/api/partii", api_partii)
    app.router.add_post("/play/api/level", api_level)
    app.router.add_post("/play/api/partiya/start", api_partiya_start)
    app.router.add_post("/play/api/partiya/move", api_partiya_move)
    app.router.add_get("/play", to_index)
    app.router.add_get("/play/", index)
    # без папки фронта бот всё равно должен работать (17.11 её не было в Dockerfile — бот падал)
    if PLAY_DIR.is_dir():
        app.router.add_static("/play/", PLAY_DIR)
    else:
        logging.error("Mini App: нет папки %s — проверь COPY в Dockerfile", PLAY_DIR)
    logging.info("Mini App «Шах и чат»: /play/")
