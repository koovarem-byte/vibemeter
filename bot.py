import asyncio
import os

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db
from handlers import router


# =========================
# HEALTH SERVER FOR RENDER
# =========================

async def health(request):
    return web.Response(text="OK")


async def start_web_server():
    app = web.Application()

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    port = int(os.getenv("PORT", "10000"))

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=port,
    )

    await site.start()

    print(f"HTTP server started on port {port}")

    return runner


# =========================
# TELEGRAM BOT
# =========================

async def start_bot():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode="HTML"
        )
    )

    dp = Dispatcher()

    dp.include_router(router)

    await init_db()

    print("Bot started")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


# =========================
# MAIN
# =========================

async def main():
    web_runner = await start_web_server()

    try:
        await start_bot()
    finally:
        await web_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())