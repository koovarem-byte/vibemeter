"""Проверка хостинга: видит ли он Telegram и базу. Секреты не печатает.

Запуск на сервере: python deploy/check_telegram.py
(BOT_TOKEN и DATABASE_URL должны быть в окружении или .env)
"""

import asyncio
import os
import socket
import sys
import time
import urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def public_ip():
    try:
        return urllib.request.urlopen("https://api.ipify.org", timeout=8).read().decode()
    except Exception as exc:
        return f"не определился ({type(exc).__name__})"


def telegram():
    token = os.getenv("BOT_TOKEN", "")
    url = f"https://api.telegram.org/bot{token}/getMe"
    started = time.time()
    try:
        data = urllib.request.urlopen(url, timeout=10).read()
        ok = b'"ok":true' in data
        return f"{'✅ отвечает' if ok else '⚠️ ответил, но не ok'} за {time.time() - started:.1f} с"
    except Exception as exc:
        return f"❌ недоступен ({type(exc).__name__})"


async def database():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return "⚠️ DATABASE_URL не задан"
    import asyncpg
    try:
        conn = await asyncpg.connect(dsn, ssl="require", timeout=15)
        await conn.fetchval("SELECT 1")
        await conn.close()
        return "✅ подключается"
    except Exception as exc:
        return f"❌ не подключается ({type(exc).__name__})"


def main():
    print("IP сервера:      ", public_ip())
    print("Хост:            ", socket.gethostname())
    print("Telegram API:    ", telegram())
    print("База Neon:       ", asyncio.run(database()))


if __name__ == "__main__":
    sys.exit(main())
