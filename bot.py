import asyncio
import logging
import os
import secrets
import signal

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import ExceptionMessageFilter
from aiogram.types import BotCommand, MenuButtonCommands, MenuButtonWebApp, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

from config import ADMIN_ID, BOT_TOKEN
from database import init_db, close_db
from handlers import router, ban_middleware, flood_middleware
import admin
import trainer
from webapp_api import setup_webapp
from chess_api import setup_play
import chessdaily
import ui
import alerts
from fsm_storage import PgStorage


# Режим работы:
# - по умолчанию long polling: процесс сам ходит в Telegram, хостингу
#   нужен только постоянно работающий контейнер;
# - WEBHOOK_BASE_URL задан (https://адрес-приложения) → webhook.
#   Нужен, если хостинг усыпляет приложение без входящих запросов.
WEBHOOK_BASE_URL = (os.getenv("WEBHOOK_BASE_URL") or "").rstrip("/")
WEBHOOK_PATH = "/webhook"
# Telegram присылает этот секрет в заголовке, чужие запросы отбрасываются.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET") or secrets.token_urlsafe(32)

PORT = int(os.getenv("PORT", "8080"))

# Публичный HTTPS-адрес сервера бота (туннель или VPS с Caddy).
# Задан → при старте кнопка меню открывает Mini App по WEBAPP_URL/app/
WEBAPP_URL = (os.getenv("WEBAPP_URL") or "").rstrip("/")


async def health(request):
    return web.Response(text="OK")


async def ignore_not_modified(event):
    return True


def create_bot_and_dispatcher():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode="HTML"
        )
    )

    dp = Dispatcher(storage=PgStorage())
    # двойное нажатие на кнопку: Telegram отвечает «message is not modified» — это не ошибка
    dp.errors.register(ignore_not_modified, ExceptionMessageFilter(r".*message is not modified"))
    # антифлуд, бан, серия и username — на весь диспетчер (раньше висели на handlers.router)
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(flood_middleware)
        observer.outer_middleware(ban_middleware)
    # команда в режиме ввода тренажёра — выход из режима (иначе «/start play» уходил как вопрос автору)
    dp.message.outer_middleware(trainer.commands_leave_input)
    dp.include_router(admin.router)  # первым: /admin и /u_… не должны уйти в общие хендлеры
    dp.include_router(trainer.router)  # тренажёр «Шах и чат» (ТЗ 16.11)
    dp.include_router(router)

    return bot, dp


_bot_dp = None


def get_bot_and_dispatcher():
    """Один бот и диспетчер на процесс: роутеры подключаются только один раз,
    а при перезапуске после падения берём те же."""
    global _bot_dp
    if _bot_dp is None:
        _bot_dp = create_bot_and_dispatcher()
    return _bot_dp


def _emoji_vec(data: bytes):
    """Картинка 24×24 на чёрном фоне -> вектор для сравнения."""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGBA").resize((24, 24))
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    return list(bg.convert("RGB").getdata())


def _match_pack(remote: dict) -> dict:
    """{custom_emoji_id: вектор} -> {имя: custom_emoji_id}: каждую картинку пака
    сопоставляем с нашим файлом assets/emoji/pack_100/NN_имя.png (порядок в паке не важен)."""
    from pathlib import Path
    local = {}
    for f in sorted((Path(__file__).parent / "assets" / "emoji" / "pack_100").glob("*.png")):
        local[f.stem.split("_", 1)[1]] = _emoji_vec(f.read_bytes())
    pairs = []
    for name, lv in local.items():
        for eid, rv in remote.items():
            d = sum(abs(a - b) for p, q in zip(lv, rv) for a, b in zip(p, q))
            pairs.append((d, name, eid))
    pairs.sort()
    out, used = {}, set()
    for d, name, eid in pairs:
        if name not in out and eid not in used:
            out[name] = eid
            used.add(eid)
    return out


async def load_emoji_pack(bot):
    """Пак «Шах и Чат»: иконки по совпадению картинок -> ui.NEON (тексты, кнопки, меню).
    Сопоставление кэшируется в app_state, пока состав пака тот же."""
    import io
    import json
    from database import get_app_state, set_app_state
    try:
        pack = await bot.get_sticker_set(ui.EMOJI_PACK)
        ids = [st.custom_emoji_id for st in pack.stickers if st.custom_emoji_id]
        sig = ",".join(ids)
        cached = await get_app_state("emoji_map")
        mapping = None
        if cached:
            data = json.loads(cached)
            if data.get("sig") == sig:
                mapping = data["map"]
        if mapping is None:
            remote = {}
            for st in pack.stickers:
                buf = io.BytesIO()
                await bot.download(st.file_id, destination=buf)
                try:
                    remote[st.custom_emoji_id] = _emoji_vec(buf.getvalue())
                except Exception:
                    logging.warning("Эмодзи: не открылась картинка %s", st.custom_emoji_id)
            mapping = _match_pack(remote)
            await set_app_state("emoji_map", json.dumps({"sig": sig, "map": mapping}))
        n = ui.load_pack_map(mapping)
        logging.info("Эмодзи «%s»: сопоставлено %s из %s", ui.EMOJI_PACK, n, len(pack.stickers))
    except Exception:
        logging.exception("Эмодзи: пак %s не загрузился, остаются старые", ui.EMOJI_PACK)


async def setup_profile(bot):
    """Описание бота из ui.py: меняем, только если отличается."""
    try:
        if (await bot.get_my_name()).name != ui.BOT_NAME:
            await bot.set_my_name(name=ui.BOT_NAME)
        if (await bot.get_my_description()).description != ui.BOT_DESCRIPTION:
            await bot.set_my_description(description=ui.BOT_DESCRIPTION)
        if (await bot.get_my_short_description()).short_description != ui.BOT_SHORT_DESCRIPTION:
            await bot.set_my_short_description(short_description=ui.BOT_SHORT_DESCRIPTION)
    except Exception:
        logging.exception("Не удалось обновить описание бота")


async def setup_menu_button(bot):
    """Команды игры; кнопка меню — Mini App «Шах и чат» (/play/), без WEBAPP_URL — список команд."""
    try:
        await bot.set_my_commands([
            BotCommand(command="play", description="Партия"),
            BotCommand(command="daily", description="Задача дня"),
            BotCommand(command="razbor", description="Разбор моей переписки"),
            BotCommand(command="baza", description="База ходов"),
            BotCommand(command="me", description="Мой рейтинг"),
            BotCommand(command="top", description="Таблица лидеров"),
            BotCommand(command="ask", description="Вопрос автору"),
            BotCommand(command="help", description="Что это и правила"),
        ])
        if WEBAPP_URL:
            await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(
                text="Играть", web_app=WebAppInfo(url=f"{WEBAPP_URL}/play/")))
        else:
            await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    except Exception:
        logging.exception("Не удалось поставить команды и кнопку меню")


def create_app(bot, dp, webhook=True):
    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    # Mini App: страница /app/ и API /app/api/*
    setup_webapp(app, bot)
    # Mini App «Шах и чат»: /play/ и /play/api/*
    setup_play(app)

    if webhook:
        SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=WEBHOOK_SECRET,
        ).register(app, path=WEBHOOK_PATH)

    return app


# =========================
# WEBHOOK
# =========================

async def run_webhook():
    bot, dp = get_bot_and_dispatcher()

    await init_db()
    await load_emoji_pack(bot)
    import chess_api
    await chess_api.load_slots()
    await setup_menu_button(bot)
    await setup_profile(bot)
    # вайб-час и засчитывание подруг — механики знакомств, с 16.11 выключены
    chess_task = asyncio.create_task(chessdaily.loop(bot))
    alerts_task = alerts.install(bot, ADMIN_ID)

    app = create_app(bot, dp, webhook=True)

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, host="0.0.0.0", port=PORT).start()

    await bot.set_webhook(
        f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        allowed_updates=dp.resolve_used_update_types(),
    )

    print(f"Webhook mode on port {PORT}")

    try:
        await _stop.wait()
    finally:
        chess_task.cancel()
        alerts_task.cancel()
        await runner.cleanup()
        await bot.session.close()
        await close_db()


# =========================
# POLLING
# =========================

async def run_polling():
    bot, dp = get_bot_and_dispatcher()

    # health-сервер, чтобы хостинг видел, что процесс жив
    runner = web.AppRunner(create_app(bot, dp, webhook=False))
    await runner.setup()
    await web.TCPSite(runner, host="0.0.0.0", port=PORT).start()

    print(f"HTTP server started on port {PORT}")
    from database import db_host
    print(f"База: {db_host()}")

    await init_db()
    await load_emoji_pack(bot)
    import chess_api
    await chess_api.load_slots()
    await setup_menu_button(bot)
    await setup_profile(bot)
    # вайб-час и засчитывание подруг — механики знакомств, с 16.11 выключены
    chess_task = asyncio.create_task(chessdaily.loop(bot))
    alerts_task = alerts.install(bot, ADMIN_ID)

    # webhook здесь специально не снимаем: если бот уже работает
    # на хостинге, локальный polling упадёт с Conflict, а не уведёт бота.

    print("Bot started")

    try:
        # сигналы ловит run_forever, иначе после перезапуска SIGTERM терялся бы
        await dp.start_polling(bot, handle_signals=False)
    finally:
        chess_task.cancel()
        alerts_task.cancel()
        await runner.cleanup()
        await bot.session.close()
        await close_db()


_stop = None  # asyncio.Event: хостинг попросил остановиться (SIGTERM/SIGINT)


async def _stop_polling():
    try:
        await get_bot_and_dispatcher()[1].stop_polling()
    except RuntimeError:
        pass  # polling ещё не запущен — ждём перезапуска, его прервёт _stop


_last_crash_notice = 0.0


async def _tell_admin_crash(err: Exception):
    """Бот не поднялся (обычно — база): пишем админу напрямую, без базы. Не чаще раза в 30 минут."""
    global _last_crash_notice
    import html
    import time
    from database import db_host
    if time.time() - _last_crash_notice < 1800:
        return
    _last_crash_notice = time.time()
    text = (
        "⚠️ Бот не запускается и перезапускается каждые 15 секунд\n\n"
        f"Ошибка: <code>{html.escape(type(err).__name__)}: {html.escape(str(err)[:300])}</code>\n"
        f"База (DATABASE_URL): <code>{html.escape(db_host())}</code>"
    )
    try:
        tmp = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
        try:
            await tmp.send_message(ADMIN_ID, text)
        finally:
            await tmp.session.close()
    except Exception:
        logging.warning("Не удалось написать админу о падении")


async def run_forever():
    """Процесс не должен умирать: если при старте Telegram или Neon на миг
    недоступны (или что-то упало), поднимаемся заново через 15 секунд."""
    global _stop
    _stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: (_stop.set(), asyncio.ensure_future(_stop_polling())))

    while not _stop.is_set():
        try:
            await (run_webhook() if WEBHOOK_BASE_URL else run_polling())
        except Exception as err:
            logging.exception("Бот упал, перезапуск через 15 секунд")
            await _tell_admin_crash(err)
        if _stop.is_set():
            return
        try:
            await asyncio.wait_for(_stop.wait(), timeout=15)
        except asyncio.TimeoutError:
            pass


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        asyncio.run(run_forever())
    except KeyboardInterrupt:
        pass
