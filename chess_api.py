"""Mini App «Шах и чат»: страница /play/ и API /play/api/*.

Каждый запрос к API несёт заголовок X-Init-Data (Telegram.WebApp.initData), проверяем подпись.
Анкета не нужна: достаточно, чтобы человек нажал /start в боте (есть строка в users).
Старый Mini App знакомств (/app/) не трогаем.
"""

import html
import logging
import os
import random
import time
from pathlib import Path

from aiohttp import web
from aiogram.utils.web_app import safe_parse_webapp_init_data

import facts
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
    chat_place,
    chess_period_top,
    chess_profile,
    get_user,
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
    if request.path in ("/play/api/state", "/play/api/move", "/play/api/partiya/move"):
        await touch_user(user["telegram_id"])
        user = await get_user(user["telegram_id"]) or user
    else:
        await mark_seen(user["telegram_id"])
    request["user"] = user
    return await handler(request)


def first_name(name: str | None) -> str:
    return ((name or "").strip().split() or ["Игрок"])[0][:20]


def me_json(user, solved: int) -> dict:
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
        "solved": solved,
        "total": len(puzzles.PUZZLES),
    }


def puzzle_json(pid: int, number: int) -> dict:
    p = puzzles.PUZZLES[pid]
    return {
        "id": pid,
        "number": number,
        "daily": pid == puzzles.today_index(),
        "chat": p["chat"],
        "moves": [{"idx": i, "text": p["moves"][i][0]} for i in puzzles.move_order(pid)],
    }


def next_puzzle(done: set[int]):
    total = len(puzzles.PUZZLES)
    start = puzzles.today_index()
    for i in range(total):
        pid = (start + i) % total
        if pid not in done:
            return pid
    return None


async def api_state(request):
    user = request["user"]
    done = await solved_puzzles(user["telegram_id"])
    pid = next_puzzle(done)
    return web.json_response({
        "me": me_json(user, len(done)),
        "puzzle": puzzle_json(pid, len(done) + 1) if pid is not None else None,
        "daily_done": puzzles.today_index() in done,
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
        text = str(body.get("text") or "").strip()[:2000]
        stars = body.get("stars")
        stars = int(stars) if stars is not None else None
        if stars is not None and not 1 <= stars <= 5:
            raise ValueError
    except (ValueError, TypeError):
        return error("bad_request", 400)
    if len(text) < 5:
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
    new_rating = await solve_puzzle(user["telegram_id"], pid, mark, elo - before)
    if new_rating is None:
        return error("already_solved", 409)
    await log_event(user["telegram_id"], "puzzle_app", f"{pid}:{mark}")
    best = max(puzzle["moves"], key=lambda m: puzzles.DELTA[m[1]])
    done = await solved_puzzles(user["telegram_id"])
    nxt = next_puzzle(done)
    fresh = {**user, "chess_rating": new_rating}
    return web.json_response({
        "mark": mark,
        "name": rating.NAMES[mark],
        "why": why,
        "best": best[0] if best[1] != mark else None,
        "others": [{"text": t, "mark": m, "why": w} for t, m, w in puzzle["moves"] if t != move],
        "delta": new_rating - before,
        "rank_up": puzzles.rank(new_rating) != puzzles.rank(before),
        "me": me_json(fresh, len(done)),
        "puzzle": puzzle_json(nxt, len(done) + 1) if nxt is not None else None,
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
    return web.json_response({"items": items, "me": mine})


def fact_json(f) -> dict:
    return {"id": f["id"], "text": f["text"], "tip": f["tip"], "source": f["source"], "url": f.get("url")}


async def api_facts(request):
    day = facts.fact_of_day()
    rest = [f for f in facts.for_bot() if f["id"] != day["id"]]
    return web.json_response({"day": fact_json(day), "items": [fact_json(f) for f in rest]})


async def api_profile(request):
    user = request["user"]
    done = await solved_puzzles(user["telegram_id"])
    prof = await chess_profile(user["telegram_id"])
    place, total = await chat_place(user["telegram_id"])
    return web.json_response({"me": me_json(user, len(done)), **prof, "place": place, "players": total})


# ---------- партии без ИИ ----------

def option_order(game_id: int, step: int, n: int) -> list[int]:
    order = list(range(n))
    random.Random(game_id * 131 + step).shuffle(order)
    return order


def step_json(game_id: int, p: dict, step: int) -> dict:
    st = p["steps"][step]
    return {
        "n": step + 1,
        "total": len(p["steps"]),
        "her": st["her"],
        "options": [{"idx": i, "text": st["options"][i][0]} for i in option_order(game_id, step, len(st["options"]))],
    }


def partiya_meta(p: dict) -> dict:
    return {"id": p["id"], "title": p["title"], "rating": p["rating"], "intro": p["intro"], "moves": len(p["steps"])}


async def api_partii(request):
    summary = await app_games_summary(request["user"]["telegram_id"])
    items = []
    for p in sorted(partii.PARTII, key=lambda p: p["rating"]):
        done = summary.get(p["id"])
        items.append({**partiya_meta(p), "result": done and done["result"],
                      "accuracy": done and rating.accuracy(done["marks"])})
    return web.json_response({"items": items, "beta": await beta_json(request)})


async def api_partiya_start(request):
    uid = request["user"]["telegram_id"]
    try:
        p = partii.BY_ID[str((await request.json())["id"])]
    except (ValueError, KeyError, TypeError):
        return error("bad_request", 400)
    if await need_feedback(uid):
        return error("need_feedback", 403)
    g = await app_game_start(uid, p["id"])
    await log_event(uid, "partiya_start", p["id"])
    return web.json_response({"game_id": g["id"], "rated": g["rated"], "partiya": partiya_meta(p),
                              "step": step_json(g["id"], p, 0)})


async def api_partiya_move(request):
    user = request["user"]
    uid = user["telegram_id"]
    try:
        body = await request.json()
        g = await app_game_get(int(body["game_id"]), uid)
        idx = int(body["idx"])
    except (ValueError, KeyError, TypeError):
        return error("bad_request", 400)
    if not g or g["status"] != "active":
        return error("game_over", 409)
    p = partii.BY_ID.get(g["partiya"])
    step = g["step"]
    if not p or step >= len(p["steps"]) or not 0 <= idx < len(p["steps"][step]["options"]):
        return error("bad_request", 400)
    opt = p["steps"][step]["options"][idx]
    text, mark, why, reply = opt[:4]
    mated = len(opt) > 4 and opt[4] == "mate"
    moves = g["moves"] + [{"step": step, "idx": idx, "mark": mark}]
    best = max(p["steps"][step]["options"], key=lambda o: rating.SCORE[o[1]])
    out = {
        "mark": mark, "name": rating.NAMES[mark], "why": why, "reply": reply,
        "best": best[0] if best[1] != mark else None,
        "others": [{"text": o[0], "mark": o[1], "why": o[2]} for o in p["steps"][step]["options"] if o[0] != text],
    }
    last = step + 1 >= len(p["steps"])
    if not (mated or last):
        await app_game_move(g["id"], moves, step + 1)
        out["next"] = step_json(g["id"], p, step + 1)
        return web.json_response(out)
    marks = [m["mark"] for m in moves]
    result = rating.result_of(marks, mated)
    before = user["chess_rating"] or 0
    after = rating.update(before, p["rating"], rating.game_score(marks), await rated_count(uid)) if g["rated"] else before
    await app_game_finish(g["id"], uid, moves, result, before, after, g["rated"])
    await log_event(uid, "partiya_end", f"{p['id']}:{result}")
    done = await solved_puzzles(uid)
    out["final"] = {
        "result": result, "rated": g["rated"], "before": before, "after": after, "delta": after - before,
        "accuracy": rating.accuracy(marks), "marks": marks,
        "expected": round(rating.expected(before, p["rating"]) * 100),
        "rank_up": puzzles.rank(after) != puzzles.rank(before),
        "me": me_json({**user, "chess_rating": after}, len(done)),
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
    app.router.add_post("/play/api/beta/join", api_beta_join)
    app.router.add_post("/play/api/feedback", api_feedback)
    app.router.add_get("/play/api/partii", api_partii)
    app.router.add_post("/play/api/partiya/start", api_partiya_start)
    app.router.add_post("/play/api/partiya/move", api_partiya_move)
    app.router.add_get("/play", to_index)
    app.router.add_get("/play/", index)
    app.router.add_static("/play/", PLAY_DIR)
    logging.info("Mini App «Шах и чат»: /play/")
