"""
API и статика Telegram Mini App.

Страница лежит в webapp/ и открывается по /app/.
Каждый запрос к /app/api/* несёт заголовок X-Init-Data (Telegram.WebApp.initData),
подпись проверяется токеном бота, так что выдать себя за другого нельзя.
"""

import io
import logging
import time
from pathlib import Path

from aiohttp import web
from aiogram.utils.web_app import safe_parse_webapp_init_data

import ui
from config import BOT_TOKEN
from database import (
    add_like,
    add_skip,
    get_candidates,
    get_incoming_likes,
    get_mutual_likes,
    get_stats,
    get_user,
    has_like,
    is_blocked,
    touch_user,
    update_user,
)
from handlers import calculate_vibe, notify_liked, notify_mutual
from utils import is_adult

WEBAPP_DIR = Path(__file__).parent / "webapp"

# initData старше суток не принимаем
INIT_DATA_TTL = 24 * 60 * 60

ICONS = {
    "heart": "🩷", "diamond": "💎", "fire": "🔥", "crown": "👑",
    "candy": "🍭", "bolt": "⚡", "star": "⭐",
}

# Уровни по числу открытых достижений (в app.js та же лесенка)
LEVELS = ((0, "Новичок"), (2, "В теме"), (4, "Вайбер"), (6, "Звезда"))

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
        "city": person["city"],
        "interests": interests_list(person),
        "about": person["description"],
    }
    if viewer is not None:
        vibe, common = calculate_vibe(viewer, person)
        data["vibe"] = vibe
        data["common"] = common
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
    steps = list(LEVELS) + [(total, "Легенда")]
    n, name, next_at = 1, steps[0][1], steps[1][0]
    for i, (at, title) in enumerate(steps):
        if done >= at:
            n, name = i + 1, title
            next_at = steps[i + 1][0] if i + 1 < len(steps) else total
    return {"n": n, "name": name, "done": done, "total": total, "next_at": next_at}


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

    return web.json_response({
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
    return web.json_response({"candidate": person_json(candidates[0], viewer=user)})


async def api_vibe(request):
    user = request["user"]
    user_id = user["telegram_id"]

    try:
        body = await request.json()
        person_id = int(body["id"])
        action = body["action"]
    except (ValueError, KeyError, TypeError):
        return error("bad_request", 400)

    if action not in ("like", "skip") or person_id == user_id:
        return error("bad_request", 400)

    person = await get_user(person_id)
    if (
        not person
        or person["is_banned"]
        or not is_adult(person["age"])
        or await is_blocked(user_id, person_id)
        or await is_blocked(person_id, user_id)
    ):
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
            "match": person_json(person, full=True),
        })

    if is_new:
        await notify_liked(bot, person_id)

    return web.json_response({"mutual": False})


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
        try:
            file = await bot.get_file(file_id)
            buffer = io.BytesIO()
            await bot.download_file(file.file_path, destination=buffer)
        except Exception:
            logging.exception("Не удалось скачать фото %s", person_id)
            return error("not_found", 404)

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
    app.router.add_get("/app/api/vibes", api_vibes)
    app.router.add_post("/app/api/settings", api_settings)
    app.router.add_get("/app/api/photo/{person_id}", api_photo)

    app.router.add_get("/app", to_index)
    app.router.add_get("/app/", index)
    app.router.add_static("/app/", WEBAPP_DIR)
