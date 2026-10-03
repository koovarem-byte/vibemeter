from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔎 Проверить вайб"),
                KeyboardButton(text="👀 Кто поймал мой вайб"),
            ],
            [
                KeyboardButton(text="👤 Мой профиль"),
                KeyboardButton(text="📊 Статистика"),
            ],
            [
                KeyboardButton(text="🎮 Играть"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие",
    )


# =========================================================
# МЕНЮ ПОСЛЕ СОЗДАНИЯ ПРОФИЛЯ
# =========================================================

def after_profile():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔎 Проверить вайб"),
                KeyboardButton(text="👀 Кто поймал мой вайб"),
            ],
            [
                KeyboardButton(text="👤 Мой профиль"),
                KeyboardButton(text="📊 Статистика"),
            ],
            [
                KeyboardButton(text="🎮 Играть"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Что делаем?",
    )


# =========================================================
# ДЕЙСТВИЯ С ПРОФИЛЕМ
# =========================================================

def profile_actions():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💜 Вайб",
                    callback_data="like",
                ),
                InlineKeyboardButton(
                    text="👎 Мимо",
                    callback_data="skip",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💬 Задать вопрос",
                    callback_data="question",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Заблокировать",
                    callback_data="block",
                ),
            ],
        ]
    )


# =========================================================
# ВХОДЯЩИЙ ВАЙБ
# =========================================================

def incoming_actions(person_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💜 Вайб",
                    callback_data=f"incoming_like:{person_id}",
                ),
                InlineKeyboardButton(
                    text="👎 Мимо",
                    callback_data=f"incoming_skip:{person_id}",
                ),
            ],
        ]
    )


# =========================================================
# ВЗАИМНЫЙ ВАЙБ
# =========================================================

def mutual_actions(person_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Познакомиться",
                    callback_data=f"contact:{person_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔎 Смотреть дальше",
                    callback_data="browse",
                ),
            ],
        ]
    )


# =========================================================
# ИГРЫ
# =========================================================

def game_actions(game_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Играть",
                    callback_data=f"game_start:{game_id}",
                ),
            ],
        ]
    )
def game_answer_actions(
    answer_a: str,
    answer_b: str,
):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=answer_a,
                    callback_data="game_answer:a",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=answer_b,
                    callback_data="game_answer:b",
                ),
            ],
        ]
    )


# =========================================================
# ПОСЛЕ ИГРЫ
# =========================================================

def game_result_actions(person_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💜 Поймать вайб",
                    callback_data=f"game_like:{person_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👎 Мимо",
                    callback_data=f"game_skip:{person_id}",
                ),
            ],
        ]
    )