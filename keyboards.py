from aiogram.types import (
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import os

import ui


def btn(text, callback_data=None, url=None, neon=None):
    """Inline-кнопка. neon — имя эмодзи из ui.NEON для иконки."""
    extra = {"icon_custom_emoji_id": ui.icon(neon)} if neon else {}
    if url:
        return InlineKeyboardButton(text=text, url=url, **extra)
    return InlineKeyboardButton(
        text=text, callback_data=callback_data, **extra
    )


def rows(*rows_):
    return InlineKeyboardMarkup(inline_keyboard=[list(r) for r in rows_])


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

def open_app_keyboard(page: str = ""):
    """Кнопка «Открыть Вайбометр» (Mini App). None, если адрес не задан.
    Именно inline-кнопка: через неё Telegram передаёт initData."""
    base = (os.getenv("WEBAPP_URL") or "").rstrip("/")
    if not base:
        return None
    url = f"{base}/app/" + (f"#{page}" if page else "")
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=ui.BTN_OPEN_APP, web_app=WebAppInfo(url=url)
        )
    ]])


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=ui.MENU_FIND),
                KeyboardButton(text=ui.MENU_LIKES),
            ],
            [
                KeyboardButton(text=ui.MENU_PROFILE),
                KeyboardButton(text=ui.MENU_GAMES),
            ],
            [
                KeyboardButton(text=ui.MENU_STATS),
                KeyboardButton(text=ui.MENU_SETTINGS),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder=ui.MENU_PLACEHOLDER,
    )


def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=ui.CANCEL)]],
        resize_keyboard=True,
    )


# =========================================================
# АНКЕТЫ
# =========================================================

def profile_actions(person_id: int):
    """Карточка в поиске."""
    return rows(
        [
            btn(ui.BTN_LIKE, f"like:{person_id}", neon="heart"),
            btn(ui.BTN_SKIP, f"skip:{person_id}", neon="speedo"),
        ],
        [
            btn(ui.BTN_QUESTION, f"question:{person_id}", neon="chat"),
            btn(ui.BTN_REPORT, f"report:{person_id}"),
        ],
    )


def incoming_actions(person_id: int):
    """Карточка в «Мои вайбы»."""
    return rows(
        [
            btn(ui.BTN_LIKE, f"incoming_like:{person_id}", neon="heart"),
            btn(ui.BTN_SKIP, f"incoming_skip:{person_id}", neon="speedo"),
        ],
        [
            btn(ui.BTN_QUESTION, f"question:{person_id}", neon="chat"),
            btn(ui.BTN_REPORT, f"report:{person_id}"),
        ],
    )


def mutual_actions(person_id: int, username: str | None):
    """После взаимного вайба: сразу ссылка на чат, если есть username."""
    if username:
        write = btn(
            ui.BTN_WRITE,
            url=f"https://t.me/{username.lstrip('@')}",
            neon="hands",
        )
    else:
        write = btn(ui.BTN_WRITE, f"contact:{person_id}", neon="hands")

    return rows([write, btn(ui.BTN_NEXT, "browse")])


def contact_keyboard(username: str):
    return rows([
        btn(ui.BTN_WRITE, url=f"https://t.me/{username}", neon="hands"),
    ])


def liked_you_keyboard():
    return rows([
        btn(ui.BTN_VIEW, "my_vibes", neon="heart"),
        btn(ui.BTN_LATER, "dismiss"),
    ])


# =========================================================
# АНКЕТА: ВЫБОР ПОЛА
# =========================================================

def gender_keyboard():
    return rows([
        btn(ui.BTN_MALE, "gender:male"),
        btn(ui.BTN_FEMALE, "gender:female"),
    ])


def search_gender_keyboard():
    return rows(
        [
            btn(ui.BTN_SEARCH_MALE, "search_gender:male"),
            btn(ui.BTN_SEARCH_FEMALE, "search_gender:female"),
        ],
        [btn(ui.BTN_SEARCH_ALL, "search_gender:all")],
    )


# =========================================================
# СОГЛАСИЕ
# =========================================================

def consent_keyboard():
    return rows(
        [btn(ui.BTN_ACCEPT, "consent:accept", neon="heart")],
        [btn(ui.BTN_POLICY, "consent:policy")],
    )


# =========================================================
# НАСТРОЙКИ И СТАТИСТИКА
# =========================================================

def settings_keyboard():
    return rows(
        [
            btn(ui.BTN_EDIT, "edit_profile", neon="gear"),
            btn(ui.BTN_SEARCH, "search_settings"),
        ],
        [
            btn(ui.BTN_BLOCKED, "blocked_users"),
            btn(ui.BTN_DELETE, "delete_profile"),
        ],
    )


def delete_confirm_keyboard():
    return rows([
        btn(ui.BTN_DELETE_YES, "delete_confirm"),
        btn(ui.BTN_BACK, "dismiss"),
    ])


def stats_keyboard():
    return rows([btn(ui.BTN_ACHIEVEMENTS, "achievements", neon="trophy")])


# =========================================================
# ВАЙБ-ИГРА
# =========================================================

def game_actions(game_id: int):
    return rows([
        btn(ui.BTN_START_GAME, f"game_start:{game_id}", neon="gamepad"),
    ])


def game_keyboard(game_id: int, question_index: int, answer_a: str, answer_b: str):
    # варианты длинные, поэтому по одному в строке
    return rows(
        [btn(answer_a, f"game_answer:{game_id}:{question_index}:a")],
        [btn(answer_b, f"game_answer:{game_id}:{question_index}:b")],
    )


def game_result_actions(person_id: int):
    return rows(
        [
            btn(ui.BTN_LIKE, f"game_like:{person_id}", neon="heart"),
            btn(ui.BTN_PLAY_AGAIN, "play_again", neon="gamepad"),
        ],
        [btn(ui.BTN_NEXT, "browse")],
    )


# =========================================================
# ВОПРОСЫ
# =========================================================

def question_answer_keyboard(question_id: int):
    return rows([
        btn(ui.BTN_ANSWER, f"answer_q:{question_id}", neon="chat"),
    ])


# =========================================================
# ЖАЛОБЫ
# =========================================================

def report_reasons_keyboard(person_id: int):
    buttons = [
        btn(title, f"report_reason:{person_id}:{code}")
        for code, title in ui.REPORT_REASONS.items()
    ]
    buttons.append(btn(ui.BTN_HIDE, f"block:{person_id}"))
    return rows(*(buttons[i:i + 2] for i in range(0, len(buttons), 2)))


def admin_report_keyboard(person_id: int):
    return rows([
        btn(ui.BTN_BAN, f"admin_ban:{person_id}"),
        btn(ui.BTN_DISMISS, f"admin_dismiss:{person_id}"),
    ])
