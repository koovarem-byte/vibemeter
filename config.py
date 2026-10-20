import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

# Telegram ID администратора: жалобы, /admin, /ban
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)

if not ADMIN_ID:
    raise ValueError("ADMIN_ID не найден в .env")
