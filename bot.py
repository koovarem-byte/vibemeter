import asyncio
import logging
import os
import secrets
import signal

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import ExceptionMessageFilter
from aiogram.types import MenuButtonWebApp, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

from config import ADMIN_ID, BOT_TOKEN
from database import init_db, close_db
from handlers import router
import admin
from webapp_api import setup_webapp
import vibehour
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
    dp.include_router(admin.router)  # первым: /admin и /u_… не должны уйти в общие хендлеры
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


async def setup_profile(bot):
    """Описание бота из ui.py: меняем, только если отличается."""
    try:
        if (await bot.get_my_description()).description != ui.BOT_DESCRIPTION:
            await bot.set_my_description(description=ui.BOT_DESCRIPTION)
        if (await bot.get_my_short_description()).short_description != ui.BOT_SHORT_DESCRIPTION:
            await bot.set_my_short_description(short_description=ui.BOT_SHORT_DESCRIPTION)
    except Exception:
        logging.exception("Не удалось обновить описание бота")


async def setup_menu_button(bot):
    # Без WEBAPP_URL кнопку не трогаем: локально её ставит deploy/dev_tunnel.sh
    if not WEBAPP_URL:
        return
    try:
        await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(
            text="Вайбометр",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}/app/"),
        ))
        print(f"Mini App: {WEBAPP_URL}/app/")
    except Exception:
        logging.exception("Не удалось поставить кнопку Mini App")


def create_app(bot, dp, webhook=True):
    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    # Mini App: страница /app/ и API /app/api/*
    setup_webapp(app, bot)

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
    await setup_menu_button(bot)
    await setup_profile(bot)
    vibe_hour_task = asyncio.create_task(vibehour.loop(bot))
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
        vibe_hour_task.cancel()
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

    await init_db()
    await setup_menu_button(bot)
    await setup_profile(bot)
    vibe_hour_task = asyncio.create_task(vibehour.loop(bot))
    alerts_task = alerts.install(bot, ADMIN_ID)

    # webhook здесь специально не снимаем: если бот уже работает
    # на хостинге, локальный polling упадёт с Conflict, а не уведёт бота.

    print("Bot started")

    try:
        # сигналы ловит run_forever, иначе после перезапуска SIGTERM терялся бы
        await dp.start_polling(bot, handle_signals=False)
    finally:
        vibe_hour_task.cancel()
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
        except Exception:
            logging.exception("Бот упал, перезапуск через 15 секунд")
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
