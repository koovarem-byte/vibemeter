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
                KeyboardButton(text="🔎 Найти вайб"),
                KeyboardButton(text="💜 Мои вайбы"),
            ],
            [
                KeyboardButton(text="👤 Мой профиль"),
                KeyboardButton(text="🎮 Вайб-игры"),
            ],
            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="⚙️ Настройки"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие",
    )


# =========================================================
# МЕНЮ ПОСЛЕ СОЗДАНИЯ ПРОФИЛЯ
# =========================================================

def after_profile():
    return main_menu()


# =========================================================
# КАРТОЧКА ПРОФИЛЯ
# =========================================================

def profile_actions(person_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💜 Поймать вайб",
                    callback_data=f"like:{person_id}",
                ),
                InlineKeyboardButton(
                    text="👎 Мимо",
                    callback_data=f"skip:{person_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💬 Задать вопрос",
                    callback_data=f"question:{person_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Заблокировать",
                    callback_data=f"block:{person_id}",
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
                    text="💜 Поймать вайб",
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

def conversation_topics(person_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎵 Музыка",
                    callback_data=f"topic:music:{person_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎮 Игры",
                    callback_data=f"topic:games:{person_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎬 Фильмы",
                    callback_data=f"topic:movies:{person_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏀 Спорт",
                    callback_data=f"topic:sport:{person_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="😂 Рандом",
                    callback_data=f"topic:random:{person_id}",
                ),
            ],
        ]
    )


# =========================================================
# НАСТРОЙКИ
# =========================================================

def settings_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Изменить профиль",
                    callback_data="edit_profile",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔔 Уведомления",
                    callback_data="notifications",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Заблокированные",
                    callback_data="blocked_users",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить профиль",
                    callback_data="delete_profile",
                ),
            ],
        ]
    )


# =========================================================
# СТАТИСТИКА
# =========================================================

def stats_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏆 Достижения",
                    callback_data="achievements",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔥 Моя серия",
                    callback_data="streak",
                ),
            ],
        ]
    )


# =========================================================
# ВАЙБ-ИГРА
# =========================================================

def game_actions(game_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 Начать игру",
                    callback_data=f"game_start:{game_id}",
                ),
            ],
        ]
    )


def game_keyboard(
    game_id: int,
    question_index: int,
    answer_a: str,
    answer_b: str,
):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=answer_a,
                    callback_data=(
                        f"game_answer:"
                        f"{game_id}:"
                        f"{question_index}:a"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=answer_b,
                    callback_data=(
                        f"game_answer:"
                        f"{game_id}:"
                        f"{question_index}:b"
                    ),
                ),
            ],
        ]
    )


# =========================================================
# РЕЗУЛЬТАТ ИГРЫ
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
                    text="🔎 Смотреть дальше",
                    callback_data="browse",
                ),
            ],
        ]
    )


# =========================================================
# ВАЙБ ДНЯ
# =========================================================

def vibe_day_keyboard(person_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💜 Поймать вайб",
                    callback_data=f"like:{person_id}",
                ),
                InlineKeyboardButton(
                    text="👎 Мимо",
                    callback_data=f"skip:{person_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💬 Задать вопрос",
                    callback_data=f"question:{person_id}",
                ),
            ],
        ]
    )


# =========================================================
# СЛУЧАЙНЫЙ ВАЙБ
# =========================================================

def random_vibe_keyboard(person_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💜 Поймать вайб",
                    callback_data=f"like:{person_id}",
                ),
                InlineKeyboardButton(
                    text="🎲 Ещё один",
                    callback_data="random_vibe",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👎 Мимо",
                    callback_data=f"skip:{person_id}",
                ),
            ],
        ]
    )


# =========================================================
# НАВИГАЦИЯ
# =========================================================

def back_keyboard(callback_data: str = "main_menu"):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=callback_data,
                ),
            ],
        ]
    )
def cancel_edit_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="❌ Отменить")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Введи данные или отмени",
    )