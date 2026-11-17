"""Переезд @vibemeter_bot → @shahichat_bot (17.11, решение владельца).

Если в окружении задан OLD_BOT_TOKEN (токен старого бота), в том же процессе
крутится старый бот и на любое сообщение отвечает: «Мы переехали» + кнопка
в новый бот. Ссылки старых роликов (?start=pz_5, ?start=shahichat …) ведут
туда же с тем же параметром. База общая, id в Telegram у человека тот же —
рейтинг, серия и решённые задачи сохраняются.
Разовая рассылка о переезде всем из старого бота — /move в админке.
"""

import logging
import os
import re

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import ui

OLD_BOT_TOKEN = (os.getenv("OLD_BOT_TOKEN") or "").strip()

old_bot: Bot | None = None
new_username: str = ""


def new_link(arg: str | None = None) -> str:
    arg = arg if arg and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", arg) else "moved"
    return f"https://t.me/{new_username}?start={arg}"


def moved_keyboard(arg: str | None = None):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
        text=ui.BTN_MOVED, url=new_link(arg), icon_custom_emoji_id=ui.icon("knight"), style="success",
    )]])


dp = Dispatcher()


@dp.message(CommandStart())
async def old_start(message: Message, command: CommandObject):
    await message.answer(ui.moved_text(new_username), reply_markup=moved_keyboard(command.args))


@dp.message()
async def old_any(message: Message):
    await message.answer(ui.moved_text(new_username), reply_markup=moved_keyboard())


@dp.callback_query()
async def old_button(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(ui.moved_text(new_username), reply_markup=moved_keyboard())


async def run(main_bot: Bot):
    """Polling старого бота. Ничего не делает без OLD_BOT_TOKEN."""
    global old_bot, new_username
    if not OLD_BOT_TOKEN:
        return
    new_username = (await main_bot.me()).username
    old_bot = Bot(token=OLD_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    try:
        me = await old_bot.me()
        if me.username == new_username:
            logging.warning("Переезд: OLD_BOT_TOKEN — это токен нового бота, выключаю")
            return
        logging.info("Переезд: @%s пересылает в @%s", me.username, new_username)
        await dp.start_polling(old_bot, handle_signals=False)
    except Exception:
        logging.exception("Переезд: старый бот не запустился (проверь OLD_BOT_TOKEN)")
    finally:
        await old_bot.session.close()
        old_bot = None
