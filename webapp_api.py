"""
API и статика Telegram Mini App.

Страница лежит в webapp/ и открывается по /app/.
Каждый запрос к /app/api/* несёт заголовок X-Init-Data (Telegram.WebApp.initData),
подпись проверяется токеном бота, так что выдать себя за другого нельзя.
"""

import asyncio
import io
import json
import re
import logging
import time
from datetime import timezone
from pathlib import Path

from aiohttp import web
from aiogram.types import BufferedInputFile
from aiogram.utils.web_app import safe_parse_webapp_init_data

import ui
from daily import today_question
from config import BOT_TOKEN
from database import (
    add_like,
    abandon_game,
    add_report,
    add_skip,
    delete_skip,
    get_candidates,
    get_daily_answers,
    set_daily_answer,
    get_incoming_likes,
    get_latest_game,
    get_mutual_likes,
    get_stats,
    get_user,
    has_like,
    is_blocked,
    touch_user,
    update_user,
)
from handlers import (
    calculate_vibe,
    same_city,
    notify_admin_report,
    notify_liked,
    notify_mutual,
)
from games import (
    calculate_result,
    complete_game,
    get_current_question,
    save_answer,
    start_game,
)
from keyboards import open_app_keyboard
from questions import MAX_QUESTION_LENGTH, send_question
from utils import (
    is_adult,
    normalize_interests,
    valid_city,
    valid_description,
    valid_name,
)

WEBAPP_DIR = Path(__file__).parent / "webapp"

# initData старше суток не принимаем
INIT_DATA_TTL = 24 * 60 * 60

ICONS = {
    "heart": "🩷", "diamond": "💎", "fire": "🔥", "crown": "👑",
    "candy": "🍭", "bolt": "⚡", "star": "⭐",
}

MAX_PHOTO_BYTES = 8 * 1024 * 1024
MAX_INTEREST_LEN = 30

# Кеш фото в памяти: file_id → байты
_photo_cache: dict[str, bytes] = {}
PHOTO_CACHE_MAX = 200


def error(code: str, status: int):
    return web.json_response({"error": code}, status=status)


# =========================================================
# Проверка initData
# =========================================================

@web.middleware
async def auth_middleware(request, handler):
    if not request.path.startswith("/app/api/"):
        return await handler(request)

    init_data = request.headers.get("X-Init-Data", "")
    try:
        data = safe_parse_webapp_init_data(BOT_TOKEN, init_data)
    except ValueError:
        return error("bad_init_data", 401)

    if not data.user or time.time() - data.auth_date.timestamp() > INIT_DATA_TTL:
        return error("bad_init_data", 401)

    user = await get_user(data.user.id)
    if not user or user["age"] is None:
        return error("no_profile", 404)
    if user["is_banned"]:
        return error("banned", 403)

    request["user"] = user
    return await handler(request)


# =========================================================
# Сериализация
# =========================================================

def interests_list(user) -> list[str]:
    return [i.strip() for i in (user["interests"] or "").split(",") if i.strip()]


def person_json(person, viewer=None, full=False):
    data = {
        "id": person["telegram_id"],
        "name": person["full_name"],
        "age": person["age"],
        "city": (person["city"] or "").strip(),
        "interests": interests_list(person),
        "about": person["description"],
    }
    if viewer is not None:
        vibe, common = calculate_vibe(viewer, person)
        data["vibe"] = vibe
        data["common"] = common
        data["same_city"] = same_city(viewer, person)
    if full:
        # только себе и при взаимном вайбе
        data["username"] = person["username"]
        data["has_photo"] = bool(person["photo_id"])
    return data


def achievements_json(stats):
    result = []
    for emoji, name, hint, key, goal in ui.ACHIEVEMENTS:
        value = min(stats[key], goal)
        result.append({
            "icon": "💘" if name == "Сердцеед" else ICONS.get(emoji, "⭐"),
            "name": name,
            "hint": hint,
            "value": value,
            "goal": goal,
            "done": stats[key] >= goal,
        })
    return result


def level_json(done: int, total: int):
    n, name, next_at = ui.level(done, total)
    return {"n": n, "name": name, "done": done, "total": total, "next_at": next_at}


async def get_target(user_id: int, person_id: int):
    """Анкета, с которой можно взаимодействовать, иначе None."""
    if person_id == user_id:
        return None
    person = await get_user(person_id)
    if (
        not person
        or person["is_banned"]
        or not is_adult(person["age"])
        or await is_blocked(user_id, person_id)
        or await is_blocked(person_id, user_id)
    ):
        return None
    return person


async def read_body(request):
    try:
        body = await request.json()
        return body, int(body["id"])
    except (ValueError, KeyError, TypeError):
        return None, None


async def is_mutual(a: int, b: int) -> bool:
    return await has_like(a, b) and await has_like(b, a)


# =========================================================
# Маршруты
# =========================================================

async def api_me(request):
    user = request["user"]
    await touch_user(user["telegram_id"])

    stats = await get_stats(user["telegram_id"])
    done, total = ui.achievements_progress(stats)

    me = person_json(user, full=True)
    me["gender"] = user["gender"]
    me["search_gender"] = user["search_gender"] or "all"

    bot_info = await request.app["bot"].me()
    mine = (await get_daily_answers([user["telegram_id"]])).get(user["telegram_id"])

    return web.json_response({
        "bot_username": bot_info.username,
        "daily": {**today_question(), "answer": mine},
        "user": me,
        "stats": {k: int(v or 0) for k, v in stats.items()},
        "achievements": achievements_json(stats),
        "level": level_json(done, total),
    })


async def api_next(request):
    user = request["user"]
    candidates = await get_candidates(user["telegram_id"])
    if not candidates:
        return web.json_response({"candidate": None})
    person = candidates[0]
    data = person_json(person, viewer=user)
    answers = await get_daily_answers([user["telegram_id"], person["telegram_id"]])
    theirs = answers.get(person["telegram_id"])
    if theirs:
        q = today_question()
        data["daily"] = {"q": q["text"], "label": q[theirs], "match": answers.get(user["telegram_id"]) == theirs}
    return web.json_response({"candidate": data})


async def api_daily(request):
    user = request["user"]
    try:
        body = await request.json()
        answer = body["answer"]
    except (ValueError, KeyError, TypeError):
        return error("bad_request", 400)
    if answer not in ("a", "b"):
        return error("bad_request", 400)
    saved = await set_daily_answer(user["telegram_id"], answer)
    return web.json_response({"ok": True, "saved": saved})


async def api_vibe(request):
    user = request["user"]
    user_id = user["telegram_id"]

    body, person_id = await read_body(request)
    if body is None or body.get("action") not in ("like", "skip"):
        return error("bad_request", 400)
    action = body["action"]

    person = await get_target(user_id, person_id)
    if not person:
        return error("not_found", 404)

    if action == "skip":
        await add_skip(from_user=user_id, to_user=person_id)
        return web.json_response({"mutual": False})

    is_new = await add_like(from_user=user_id, to_user=person_id)
    bot = request.app["bot"]

    if await has_like(from_user=person_id, to_user=user_id):
        # в боте тоже придёт фото и кнопка «Написать»
        await notify_mutual(bot, user_id, person_id)
        return web.json_response({
            "mutual": True,
            "match": person_json(person, viewer=user, full=True),
        })

    if is_new:
        await notify_liked(bot, person_id)

    return web.json_response({"mutual": False})


async def api_question(request):
    user_id = request["user"]["telegram_id"]

    body, person_id = await read_body(request)
    text = str((body or {}).get("text") or "").strip()
    if body is None or not 0 < len(text) <= MAX_QUESTION_LENGTH:
        return error("bad_request", 400)

    if not await get_target(user_id, person_id):
        return error("not_found", 404)

    question_id = await send_question(
        bot=request.app["bot"],
        from_user=user_id,
        to_user=person_id,
        text=text,
    )
    if question_id is None:
        return error("not_delivered", 502)
    return web.json_response({"ok": True})


async def api_report(request):
    user_id = request["user"]["telegram_id"]

    body, person_id = await read_body(request)
    code = (body or {}).get("reason")
    if body is None or code not in ui.REPORT_REASONS:
        return error("bad_request", 400)

    if not await get_target(user_id, person_id):
        return error("not_found", 404)

    reason = ui.REPORT_REASONS[code]
    # add_report заодно скрывает анкету для автора жалобы
    if await add_report(user_id, person_id, reason):
        await notify_admin_report(request.app["bot"], user_id, person_id, reason)
    return web.json_response({"ok": True})


async def api_undo(request):
    """Вернуть анкету после «Мимо»."""
    user_id = request["user"]["telegram_id"]
    body, person_id = await read_body(request)
    if body is None:
        return error("bad_request", 400)

    person = await get_target(user_id, person_id)
    if not person or not await delete_skip(user_id, person_id):
        return error("not_found", 404)
    return web.json_response({"candidate": person_json(person, viewer=request["user"])})


async def api_profile(request):
    """Правка анкеты. Возраст и пол меняются только в боте (проверка 18+)."""
    user = request["user"]
    try:
        body = await request.json()
    except ValueError:
        return error("bad_request", 400)
    if not isinstance(body, dict):
        return error("bad_request", 400)

    changes = {}

    if "name" in body:
        name = str(body["name"] or "").strip()
        if not valid_name(name):
            return error("bad_name", 400)
        changes["full_name"] = name

    if "city" in body:
        city = str(body["city"] or "").strip()
        if not valid_city(city):
            return error("bad_city", 400)
        changes["city"] = city

    if "about" in body:
        about = str(body["about"] or "").strip()
        if not about or not valid_description(about):
            return error("bad_about", 400)
        changes["description"] = about

    if "interests" in body:
        items = body["interests"]
        if not isinstance(items, list):
            return error("bad_interests", 400)
        # запятая внутри тега сломала бы хранение строкой
        cleaned = [
            re.sub(r"\s+", " ", str(i).replace(",", " ")).strip()[:MAX_INTEREST_LEN]
            for i in items
        ]
        interests = normalize_interests(", ".join(i for i in cleaned if i))
        if not interests:
            return error("bad_interests", 400)
        changes["interests"] = interests

    if "search_gender" in body:
        if body["search_gender"] not in ("male", "female", "all"):
            return error("bad_request", 400)
        changes["search_gender"] = body["search_gender"]

    if not changes:
        return error("bad_request", 400)

    await update_user(user["telegram_id"], **changes)
    return web.json_response({"ok": True})


async def api_upload_photo(request):
    """Новое фото анкеты: шлём его пользователю в чат с ботом и берём file_id."""
    user_id = request["user"]["telegram_id"]

    if request.content_length and request.content_length > MAX_PHOTO_BYTES + 4096:
        return error("too_big", 413)

    try:
        reader = await request.multipart()
        part = await reader.next()
    except Exception:
        return error("bad_request", 400)
    if part is None or part.name != "photo":
        return error("bad_request", 400)

    # читаем кусками, чтобы не принять гигантский файл целиком
    chunks, size = [], 0
    while chunk := await part.read_chunk(64 * 1024):
        size += len(chunk)
        if size > MAX_PHOTO_BYTES:
            return error("too_big", 413)
        chunks.append(chunk)
    data = b"".join(chunks)
    if not data:
        return error("bad_request", 400)
    # JPEG, PNG или WEBP — по сигнатуре, а не по имени файла
    if not (data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n"
            or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")):
        return error("bad_type", 415)

    bot = request.app["bot"]
    try:
        message = await bot.send_photo(
            user_id,
            photo=BufferedInputFile(data, filename="photo.jpg"),
            caption=ui.PHOTO_UPDATED,
            disable_notification=True,
        )
    except Exception:
        logging.exception("Не удалось загрузить фото %s", user_id)
        return error("upload_failed", 502)

    old = request["user"]["photo_id"]
    _photo_cache.pop(old, None)
    await update_user(user_id, photo_id=message.photo[-1].file_id)
    return web.json_response({"ok": True})


# =========================================================
# Игра «Что выберешь?» (единая очередь для всех игроков Mini App)
# =========================================================

# user_id -> время входа в очередь
game_queue: dict[int, float] = {}
QUEUE_TTL = 15 * 60          # дольше не ждём
RESULT_TTL = 15 * 60         # результат показываем 15 минут после игры
STUCK_AFTER = 10 * 60        # соперник молчит дольше — можно начать новую


def _clean_queue():
    now = time.time()
    for uid in [u for u, t in game_queue.items() if now - t > QUEUE_TTL]:
        game_queue.pop(uid, None)


def _age_seconds(game) -> float:
    created = game["created_at"]
    if created is None:
        return 0
    if created.tzinfo is None:
        # в базе время без пояса, Neon пишет его в UTC
        created = created.replace(tzinfo=timezone.utc)
    return max(0, time.time() - created.timestamp())


async def _opponent_json(user, opponent_id: int):
    person = await get_user(opponent_id)
    if not person:
        return None
    return person_json(person, viewer=user)


async def game_state_for(request) -> dict:
    """Что показывать игроку: idle / waiting / playing / waiting_opponent / finished."""
    user = request["user"]
    user_id = user["telegram_id"]
    _clean_queue()

    game = await get_latest_game(user_id)

    if game and game["status"] == "waiting":
        opponent_id = (
            game["user_two"] if game["user_one"] == user_id else game["user_one"]
        )
        question = await get_current_question(game["id"], user_id)
        answered = 5 if question is None else question["index"]
        result = await complete_game(game["id"]) if question is None else None
        if result:
            return await _finished_state(user, game, result)
        base = {
            "game_id": game["id"],
            "opponent": await _opponent_json(user, opponent_id),
            "answered": answered,
            "total": 5,
        }
        if question is None:
            base["state"] = "waiting_opponent"
            base["stuck"] = _age_seconds(game) > STUCK_AFTER
            return base
        base["state"] = "playing"
        base["question"] = {
            "index": question["index"],
            "text": question["question"],
            "a": question["a"],
            "b": question["b"],
        }
        return base

    if game and game["status"] == "finished" and _age_seconds(game) < RESULT_TTL:
        result = await calculate_result(game["id"])
        if result:
            return await _finished_state(user, game, result)

    if user_id in game_queue:
        return {"state": "waiting"}
    return {"state": "idle"}


async def _finished_state(user, game, result):
    user_id = user["telegram_id"]
    opponent_id = (
        game["user_two"] if game["user_one"] == user_id else game["user_one"]
    )
    return {
        "state": "finished",
        "game_id": game["id"],
        "opponent": await _opponent_json(user, opponent_id),
        "matches": result["matches"],
        "total": result["total"],
        "percentage": result["percentage"],
    }


async def api_game_state(request):
    return web.json_response(await game_state_for(request))


async def api_game_join(request):
    user = request["user"]
    user_id = user["telegram_id"]
    _clean_queue()

    game = await get_latest_game(user_id)
    if game and game["status"] == "waiting":
        # уже играет; новую можно, только если соперник завис
        if _age_seconds(game) > STUCK_AFTER:
            await abandon_game(game["id"])
        else:
            return web.json_response(await game_state_for(request))

    # свободный соперник: взрослый, не забаненный, не заблокированный
    opponent_id = None
    for uid in list(game_queue):
        if uid == user_id:
            continue
        other = await get_user(uid)
        if (
            other and not other["is_banned"] and is_adult(other["age"])
            and not await is_blocked(user_id, uid)
            and not await is_blocked(uid, user_id)
        ):
            opponent_id = uid
            break
        game_queue.pop(uid, None)

    if opponent_id is None:
        game_queue[user_id] = time.time()
        return web.json_response({"state": "waiting"})

    game_queue.pop(opponent_id, None)
    game_queue.pop(user_id, None)
    await start_game(opponent_id, user_id)

    # соперник мог закрыть приложение: зовём его обратно через бота
    keyboard = open_app_keyboard("games")
    try:
        await request.app["bot"].send_message(
            opponent_id,
            ui.GAME_FOUND_PING,
            reply_markup=keyboard,
        )
    except Exception:
        logging.info("Не удалось позвать соперника %s", opponent_id)

    return web.json_response(await game_state_for(request))


async def api_game_leave(request):
    user_id = request["user"]["telegram_id"]
    game_queue.pop(user_id, None)
    return web.json_response({"state": "idle"})


async def api_game_answer(request):
    user_id = request["user"]["telegram_id"]
    try:
        body = await request.json()
        game_id = int(body["game_id"])
        index = int(body["index"])
        answer = body["answer"]
    except (ValueError, KeyError, TypeError):
        return error("bad_request", 400)

    if not await save_answer(game_id, user_id, index, answer):
        return error("rejected", 409)

    state = await game_state_for(request)
    # второму игроку напомним через бота, что результат готов
    if state.get("state") == "finished" and state.get("opponent"):
        try:
            await request.app["bot"].send_message(
                state["opponent"]["id"],
                ui.GAME_RESULT_PING,
                reply_markup=open_app_keyboard("games"),
            )
        except Exception:
            pass
    return web.json_response(state)


async def api_vibes(request):
    user = request["user"]
    user_id = user["telegram_id"]

    incoming = await get_incoming_likes(user_id)
    mutual = await get_mutual_likes(user_id)

    return web.json_response({
        "incoming": [person_json(p, viewer=user) for p in incoming[:30]],
        "mutual": [person_json(p, full=True) for p in mutual],
    })


async def api_settings(request):
    user = request["user"]
    try:
        body = await request.json()
    except ValueError:
        return error("bad_request", 400)

    search_gender = body.get("search_gender")
    if search_gender not in ("male", "female", "all"):
        return error("bad_request", 400)

    await update_user(user["telegram_id"], search_gender=search_gender)
    return web.json_response({"ok": True})


async def api_photo(request):
    user_id = request["user"]["telegram_id"]
    try:
        person_id = int(request.match_info["person_id"])
    except ValueError:
        return error("bad_request", 400)

    # Фото: своё или человека со взаимным вайбом
    if person_id != user_id and not await is_mutual(user_id, person_id):
        return error("forbidden", 403)

    person = await get_user(person_id)
    if not person or not person["photo_id"] or person["is_banned"]:
        return error("not_found", 404)

    file_id = person["photo_id"]
    content = _photo_cache.get(file_id)

    if content is None:
        bot = request.app["bot"]
        # сеть до Telegram бывает нестабильной: пара повторов
        for attempt in range(3):
            try:
                file = await bot.get_file(file_id)
                buffer = io.BytesIO()
                await bot.download_file(file.file_path, destination=buffer)
                break
            except Exception:
                if attempt == 2:
                    logging.exception("Не удалось скачать фото %s", person_id)
                    return error("not_found", 404)
                await asyncio.sleep(1)

        content = buffer.getvalue()
        if len(_photo_cache) >= PHOTO_CACHE_MAX:
            _photo_cache.pop(next(iter(_photo_cache)))
        _photo_cache[file_id] = content

    return web.Response(
        body=content,
        content_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=3600"},
    )


# =========================================================
# Статика
# =========================================================

@web.middleware
async def no_cache_middleware(request, handler):
    response = await handler(request)
    # Telegram любит кешировать страницу, обновления должны доходить сразу
    if request.path.startswith("/app") and not request.path.startswith("/app/api/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


async def index(request):
    return web.FileResponse(WEBAPP_DIR / "index.html")


async def to_index(request):
    raise web.HTTPFound("/app/")


def setup_webapp(app: web.Application, bot):
    app["bot"] = bot
    app.middlewares.append(auth_middleware)
    app.middlewares.append(no_cache_middleware)

    app.router.add_get("/app/api/me", api_me)
    app.router.add_get("/app/api/next", api_next)
    app.router.add_post("/app/api/vibe", api_vibe)
    app.router.add_post("/app/api/daily", api_daily)
    app.router.add_get("/app/api/game/state", api_game_state)
    app.router.add_post("/app/api/game/join", api_game_join)
    app.router.add_post("/app/api/game/leave", api_game_leave)
    app.router.add_post("/app/api/game/answer", api_game_answer)
    app.router.add_post("/app/api/undo", api_undo)
    app.router.add_post("/app/api/profile", api_profile)
    app.router.add_post("/app/api/upload_photo", api_upload_photo)
    app.router.add_post("/app/api/question", api_question)
    app.router.add_post("/app/api/report", api_report)
    app.router.add_get("/app/api/vibes", api_vibes)
    app.router.add_post("/app/api/settings", api_settings)
    app.router.add_get("/app/api/photo/{person_id}", api_photo)

    app.router.add_get("/app", to_index)
    app.router.add_get("/app/", index)
    app.router.add_static("/app/", WEBAPP_DIR)
