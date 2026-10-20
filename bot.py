import asyncio
import logging
import os
import secrets

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import MenuButtonWebApp, WebAppInfo
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

from config import BOT_TOKEN
from database import init_db, close_db
from handlers import router
from webapp_api import setup_webapp


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


def create_bot_and_dispatcher():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode="HTML"
        )
    )

    dp = Dispatcher()
    dp.include_router(router)

    return bot, dp


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
    bot, dp = create_bot_and_dispatcher()

    await init_db()
    await setup_menu_button(bot)

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
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await bot.session.close()
        await close_db()


# =========================
# POLLING
# =========================

async def run_polling():
    bot, dp = create_bot_and_dispatcher()

    # health-сервер, чтобы хостинг видел, что процесс жив
    runner = web.AppRunner(create_app(bot, dp, webhook=False))
    await runner.setup()
    await web.TCPSite(runner, host="0.0.0.0", port=PORT).start()

    print(f"HTTP server started on port {PORT}")

    await init_db()
    await setup_menu_button(bot)

    # webhook здесь специально не снимаем: если бот уже работает
    # на хостинге, локальный polling упадёт с Conflict, а не уведёт бота.

    print("Bot started")

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()
        await close_db()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if WEBHOOK_BASE_URL:
        asyncio.run(run_webhook())
    else:
        asyncio.run(run_polling())
