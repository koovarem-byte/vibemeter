"""«Шах и чат»: раз в день напоминание о задаче дня.

В 13:00 по Москве пишем только тем, кто уже играл, заходил за последние
7 дней, сегодня ещё не решал и не отключал напоминание. Не чаще раза в день
(claim_once). Кнопка «Не напоминать» отключает навсегда, /chess_on — вернуть.
"""

import asyncio
import logging
from datetime import datetime

from aiogram.exceptions import TelegramForbiddenError

import puzzles
import ui
from database import chess_reminder_recipients, claim_once, set_chess_notify
from keyboards import chess_reminder_keyboard

HOUR = 13
DAYS = 7


async def notify_all(bot):
    sent = 0
    for row in await chess_reminder_recipients(DAYS, len(puzzles.PUZZLES)):
        try:
            await bot.send_message(
                row["telegram_id"],
                ui.chess_reminder(row["chess_rating"], puzzles.rank(row["chess_rating"])),
                reply_markup=chess_reminder_keyboard(),
            )
            sent += 1
        except TelegramForbiddenError:
            await set_chess_notify(row["telegram_id"], False)
        except Exception:
            logging.warning("Задача дня: не отправилось %s", row["telegram_id"])
        await asyncio.sleep(0.05)
    logging.info("Задача дня: напоминание ушло %s людям", sent)


async def loop(bot):
    while True:
        try:
            now = datetime.now(puzzles.MSK)
            if now.hour == HOUR and await claim_once("chess_daily_notified", now.date().isoformat()):
                await notify_all(bot)
        except asyncio.CancelledError:
            raise
        except Exception:
            logging.exception("Задача дня: ошибка в цикле")
        await asyncio.sleep(60)
