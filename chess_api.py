"""Mini App «Шах и чат»: страница /play/ и API /play/api/*.

Каждый запрос к API несёт заголовок X-Init-Data (Telegram.WebApp.initData), проверяем подпись.
Анкета не нужна: достаточно, чтобы человек нажал /start в боте (есть строка в users).
Старый Mini App знакомств (/app/) не трогаем.
"""

import logging
import time
from pathlib import Path

from aiohttp import web
from aiogram.utils.web_app import safe_parse_webapp_init_data

import facts
import puzzles
from config import BOT_TOKEN
from database import (
    chat_place,
    chess_period_top,
    chess_profile,
    get_user,
    log_event,
    mark_seen,
    solve_puzzle,
    solved_puzzles,
)

PLAY_DIR = Path(__file__).parent / "webapp_chess"
INIT_DATA_TTL = 24 * 60 * 60
PERIODS = {"day": 1, "week": 7, "all": None}


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
    request["user"] = user
    await mark_seen(user["telegram_id"])
    return await handler(request)


def first_name(name: str | None) -> str:
    return ((name or "").strip().split() or ["Игрок"])[0][:20]


def me_json(user, solved: int) -> dict:
    rating = user["chess_rating"] or 0
    nxt = puzzles.next_rank(rating)
    prev = max([limit for limit, _ in puzzles.RANKS if limit <= rating] or [0])
    return {
        "name": first_name(user["full_name"]),
        "rating": rating,
        "rank": puzzles.rank(rating),
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
    })


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
    rating = await solve_puzzle(user["telegram_id"], pid, mark, puzzles.DELTA[mark])
    if rating is None:
        return error("already_solved", 409)
    await log_event(user["telegram_id"], "puzzle_app", f"{pid}:{mark}")
    best = max(puzzle["moves"], key=lambda m: puzzles.DELTA[m[1]])
    done = await solved_puzzles(user["telegram_id"])
    nxt = next_puzzle(done)
    fresh = {**user, "chess_rating": rating}
    return web.json_response({
        "mark": mark,
        "name": puzzles.NAMES[mark],
        "why": why,
        "best": best[0] if best[1] != mark else None,
        "delta": rating - before,
        "rank_up": puzzles.rank(rating) != puzzles.rank(before),
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
    app.router.add_get("/play", to_index)
    app.router.add_get("/play/", index)
    app.router.add_static("/play/", PLAY_DIR)
    logging.info("Mini App «Шах и чат»: /play/")
