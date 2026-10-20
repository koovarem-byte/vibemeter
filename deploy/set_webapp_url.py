"""Ставит кнопку меню «Вайбометр» на адрес Mini App. Использует dev_tunnel.sh."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot  # noqa: E402
from aiogram.types import MenuButtonWebApp, WebAppInfo  # noqa: E402

from config import BOT_TOKEN  # noqa: E402


async def main(base_url: str):
    url = f"{base_url.rstrip('/')}/app/"
    bot = Bot(BOT_TOKEN)
    try:
        # сеть с Mac нестабильная, пробуем несколько раз
        for attempt in range(5):
            try:
                await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(
                    text="Вайбометр", web_app=WebAppInfo(url=url),
                ))
                print(f"✅ Кнопка Mini App → {url}")
                return
            except Exception as exc:
                print(f"Попытка {attempt + 1}: {type(exc).__name__}, ещё раз…")
                await asyncio.sleep(3)
        print("❌ Не удалось поставить кнопку")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
