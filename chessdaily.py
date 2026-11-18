"""«Шах и чат»: раз в день напоминание о задаче дня.

В 13:00 по Москве пишем только тем, кто уже играл, заходил за последние
7 дней, сегодня ещё не решал и не отключал напоминание. В 20:00 — «серия сгорит
в полночь» тем, у кого серия от 2 дней и сегодня ещё не заходили (их в 13:00
не трогаем: одному человеку не больше одного сообщения в день).
Кнопка «Не напоминать» отключает оба, /chess_on — вернуть.
В 18:00 — бета-тестерам без отзыва (в тесте больше суток) один раз за всё время
напоминание «Оставить отзыв», кнопка открывает Mini App сразу на форме.
"""

import asyncio
import logging
from datetime import datetime

from aiogram.exceptions import TelegramForbiddenError

import puzzles
import ui
from database import (beta_feedback_recipients, chess_reminder_recipients, claim_once, log_event,
                      set_chess_notify, streak_save_recipients)
from keyboards import chess_reminder_keyboard, feedback_keyboard

HOUR = 13
FEEDBACK_HOUR = 18   # бета: один раз напомнить об отзыве (сутки в тесте, отзыва нет)
EVENING_HOUR = 20
DAYS = 7


async def notify_all(bot, evening: bool = False):
    sent = 0
    rows = await (streak_save_recipients(len(puzzles.PUZZLES)) if evening
                  else chess_reminder_recipients(DAYS, len(puzzles.PUZZLES)))
    for row in rows:
        text = (ui.streak_reminder(row["streak_days"], row["chess_rating"]) if evening
                else ui.chess_reminder(row["chess_rating"], puzzles.rank(row["chess_rating"])))
        try:
            await bot.send_message(row["telegram_id"], text, reply_markup=chess_reminder_keyboard())
            sent += 1
        except TelegramForbiddenError:
            await set_chess_notify(row["telegram_id"], False)
        except Exception:
            logging.warning("Задача дня: не отправилось %s", row["telegram_id"])
        await asyncio.sleep(0.05)
    logging.info("%s: напоминание ушло %s людям", "Серия" if evening else "Задача дня", sent)


async def remind_feedback(bot):
    markup = feedback_keyboard()
    if not markup:
        return
    sent = 0
    for uid in await beta_feedback_recipients():
        await log_event(uid, "beta_fb_remind")
        try:
            await bot.send_message(uid, ui.beta_feedback_reminder(), reply_markup=markup)
            sent += 1
        except TelegramForbiddenError:
            pass
        except Exception:
            logging.warning("Отзыв беты: не отправилось %s", uid)
        await asyncio.sleep(0.05)
    logging.info("Отзыв беты: напоминание ушло %s людям", sent)


async def loop(bot):
    while True:
        try:
            now = datetime.now(puzzles.MSK)
            if now.hour == HOUR and await claim_once("chess_daily_notified", now.date().isoformat()):
                await notify_all(bot)
            if now.hour == FEEDBACK_HOUR and await claim_once("beta_feedback_notified", now.date().isoformat()):
                await remind_feedback(bot)
            if now.hour == EVENING_HOUR and await claim_once("chess_streak_notified", now.date().isoformat()):
                await notify_all(bot, evening=True)
        except asyncio.CancelledError:
            raise
        except Exception:
            logging.exception("Задача дня: ошибка в цикле")
        await asyncio.sleep(60)
