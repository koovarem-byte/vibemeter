"""Ошибки бота приходят админу в Telegram.

Любая запись logging уровня ERROR (наши logging.exception, падения
хендлеров aiogram, ошибки aiohttp) попадает в очередь, фоновая задача
отправляет её админу. Одинаковые ошибки — не чаще раза в 10 минут,
всего не больше 20 в час, чтобы при поломке не завалить чат.
"""

import asyncio
import html
import logging
import time
import traceback

REPEAT_SECONDS = 10 * 60
HOURLY_LIMIT = 20


class TelegramAlertHandler(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=100)

    def emit(self, record):
        # человек заблокировал бота или удалил аккаунт — это не сбой
        if record.exc_info and record.exc_info[1] is not None:
            text = str(record.exc_info[1])
            if "bot was blocked by the user" in text or "user is deactivated" in text:
                return
        try:
            self.queue.put_nowait(record)
        except Exception:
            pass  # очередь полна или нет цикла — молча пропускаем


def _format(record) -> str:
    text = f"⚠️ <b>Ошибка в боте</b>\n<code>{html.escape(record.name)}</code>\n{html.escape(record.getMessage()[:500])}"
    if record.exc_info:
        tb = "".join(traceback.format_exception(*record.exc_info))
        text += f"\n\n<pre>{html.escape(tb[-2500:])}</pre>"
    return text[:4000]


async def alert_loop(bot, admin_id: int, handler: TelegramAlertHandler):
    last_sent: dict[tuple, float] = {}
    hour_start, hour_count = time.time(), 0

    while True:
        record = await handler.queue.get()
        now = time.time()
        signature = (record.name, record.pathname, record.lineno)
        if now - last_sent.get(signature, 0) < REPEAT_SECONDS:
            continue
        if now - hour_start > 3600:
            hour_start, hour_count = now, 0
        if hour_count >= HOURLY_LIMIT:
            continue

        last_sent[signature] = now
        hour_count += 1
        try:
            await bot.send_message(admin_id, _format(record))
        except Exception as err:
            # не через logging, иначе ошибка отправки зациклится
            print(f"alerts: не отправилось админу: {err}")


def install(bot, admin_id: int) -> asyncio.Task:
    handler = TelegramAlertHandler()
    logging.getLogger().addHandler(handler)
    return asyncio.create_task(alert_loop(bot, admin_id, handler))
