from aiogram.types import (
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import os
from urllib.parse import quote

import ui


# Цвет кнопки (Telegram даёт только три): синий — главное действие,
# зелёный — написать/начать, красный — 18+, жалоба, удаление.
PRIMARY, SUCCESS, DANGER = "primary", "success", "danger"


def btn(text, callback_data=None, url=None, neon=None, style=None):
    """Inline-кнопка. neon — имя эмодзи из ui.NEON для иконки, style — цвет."""
    extra = {"icon_custom_emoji_id": ui.icon(neon)} if neon else {}
    if style:
        extra["style"] = style
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
            text=ui.BTN_OPEN_APP, web_app=WebAppInfo(url=url),
            icon_custom_emoji_id=ui.icon("spark"), style=PRIMARY,
        )
    ]])


def menu_btn(text):
    """Кнопка нижнего меню с неоновой иконкой."""
    return KeyboardButton(
        text=text, icon_custom_emoji_id=ui.icon(ui.MENU_ICONS[text]), style=PRIMARY,
    )


def story_button(percent: int, name: str, matches=None, total=None):
    """«Картинка для сторис»: экран #card в Mini App. None без WEBAPP_URL."""
    base = (os.getenv("WEBAPP_URL") or "").rstrip("/")
    if not base:
        return None
    page = f"card?p={int(percent)}&n={quote((name or '')[:40])}"
    if total:
        page += f"&m={int(matches)}&t={int(total)}"
    return InlineKeyboardButton(
        text=ui.BTN_STORY,
        web_app=WebAppInfo(url=f"{base}/app/#{page}"),
        icon_custom_emoji_id=ui.icon("spark"),
    )


def vibe_hour_keyboard():
    """Напоминание о вайб-часе: зайти и отключить."""
    first = open_app_keyboard("search")
    go = (
        InlineKeyboardButton(text=ui.BTN_VH_GO, web_app=first.inline_keyboard[0][0].web_app, icon_custom_emoji_id=ui.icon("bolt"), style=PRIMARY)
        if first else btn(ui.BTN_VH_GO, "browse", neon="bolt", style=PRIMARY)
    )
    return rows([go], [btn(ui.BTN_VH_OFF, "vh_off")])


def vibe_hour_on_keyboard():
    return rows([btn(ui.BTN_VH_ON, "vh_on")])


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                menu_btn(ui.MENU_FIND),
                menu_btn(ui.MENU_LIKES),
            ],
            [
                menu_btn(ui.MENU_PROFILE),
                menu_btn(ui.MENU_GAMES),
            ],
            [
                menu_btn(ui.MENU_STATS),
                menu_btn(ui.MENU_SETTINGS),
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
            btn(ui.BTN_LIKE, f"like:{person_id}", neon="heart", style=PRIMARY),
            btn(ui.BTN_SKIP, f"skip:{person_id}", neon="speedo"),
        ],
        [
            btn(ui.BTN_QUESTION, f"question:{person_id}", neon="chat"),
            btn(ui.BTN_REPORT, f"report:{person_id}", style=DANGER),
        ],
    )


def incoming_actions(person_id: int):
    """Карточка в «Мои вайбы»."""
    return rows(
        [
            btn(ui.BTN_LIKE, f"incoming_like:{person_id}", neon="heart", style=PRIMARY),
            btn(ui.BTN_SKIP, f"incoming_skip:{person_id}", neon="speedo"),
        ],
        [
            btn(ui.BTN_QUESTION, f"question:{person_id}", neon="chat"),
            btn(ui.BTN_REPORT, f"report:{person_id}", style=DANGER),
        ],
    )


def play_button(person_id: int):
    """«Сыграть вместе» после мэтча — по желанию, игры на двоих в Mini App."""
    base = (os.getenv("WEBAPP_URL") or "").rstrip("/")
    if not base:
        return None
    return InlineKeyboardButton(
        text=ui.BTN_PLAY_TOGETHER,
        web_app=WebAppInfo(url=f"{base}/app/#games?with={int(person_id)}"),
        icon_custom_emoji_id=ui.icon("gamepad"),
    )


def mutual_actions(person_id: int, username: str | None, story=None):
    """После взаимного вайба: сразу ссылка на чат, если есть username."""
    if username:
        write = btn(
            ui.BTN_WRITE,
            url=f"https://t.me/{username.lstrip('@')}",
            neon="hands",
            style=SUCCESS,
        )
    else:
        write = btn(ui.BTN_WRITE, f"contact:{person_id}", neon="hands", style=SUCCESS)

    keyboard = [[write, btn(ui.BTN_NEXT, "browse", neon="speedo")]]
    for extra in (play_button(person_id), story):
        if extra:
            keyboard.append([extra])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def contact_keyboard(username: str):
    return rows([
        btn(ui.BTN_WRITE, url=f"https://t.me/{username}", neon="hands", style=SUCCESS),
    ])


def liked_you_keyboard():
    return rows([
        btn(ui.BTN_VIEW, "my_vibes", neon="heart", style=PRIMARY),
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
        [btn(ui.BTN_ACCEPT, "consent:accept", neon="heart", style=DANGER)],
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
            btn(ui.BTN_DELETE, "delete_profile", style=DANGER),
        ],
        [btn(ui.BTN_CHANNEL, url=ui.CHANNEL_URL)],
    )


def delete_confirm_keyboard():
    return rows([
        btn(ui.BTN_DELETE_YES, "delete_confirm", style=DANGER),
        btn(ui.BTN_BACK, "dismiss"),
    ])


def stats_keyboard():
    return rows([btn(ui.BTN_ACHIEVEMENTS, "achievements", neon="trophy")])


# =========================================================
# ВАЙБ-ИГРА
# =========================================================

def game_actions(game_id: int):
    return rows([
        btn(ui.BTN_START_GAME, f"game_start:{game_id}", neon="gamepad", style=SUCCESS),
    ])


def game_keyboard(game_id: int, question_index: int, answer_a: str, answer_b: str):
    # варианты длинные, поэтому по одному в строке
    return rows(
        [btn(answer_a, f"game_answer:{game_id}:{question_index}:a")],
        [btn(answer_b, f"game_answer:{game_id}:{question_index}:b")],
    )


def game_result_actions(person_id: int, story=None):
    keyboard = [
        [
            btn(ui.BTN_LIKE, f"game_like:{person_id}", neon="heart", style=PRIMARY),
            btn(ui.BTN_PLAY_AGAIN, "play_again", neon="gamepad"),
        ],
        [btn(ui.BTN_NEXT, "browse", neon="speedo")],
    ]
    if story:
        keyboard.append([story])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# =========================================================
# ВОПРОСЫ
# =========================================================

def question_answer_keyboard(question_id: int):
    """Ответить, вайб автору (id автора не раскрываем — только id вопроса), жалоба."""
    return rows(
        [
            btn(ui.BTN_ANSWER, f"answer_q:{question_id}", neon="chat", style=PRIMARY),
            btn(ui.BTN_VIBE_BACK, f"q_like:{question_id}", neon="heart"),
        ],
        [btn(ui.BTN_REPORT, f"q_report:{question_id}", style=DANGER)],
    )


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
        btn(ui.BTN_BAN, f"admin_ban:{person_id}", style=DANGER),
        btn(ui.BTN_DISMISS, f"admin_dismiss:{person_id}"),
    ])


# =========================================================
# РАССЫЛКА
# =========================================================

def broadcast_keyboard(person: dict, bot_username: str, chosen: str | None = None):
    """Голосование + одна кнопка по состоянию человека + отписка."""
    keyboard = [
        [btn(
            ("✓ " if key == chosen else "") + label,
            f"vote:{key}",
            style=SUCCESS if key == chosen else None,
        )]
        for key, (label, _) in ui.FEATURES.items()
    ]
    # deep link в этого же бота: в /sources видно, сколько пришли из рассылки (метка bc)
    if person["age"] is None:
        keyboard.append([
            btn(ui.BTN_FILL_PROFILE, url=f"https://t.me/{bot_username}?start=bc", style=PRIMARY),
            btn(ui.BTN_VT, url=f"https://t.me/{bot_username}?start=vt"),
        ])
    elif person["photo_id"] and person["incoming"]:
        keyboard.append([btn(ui.BTN_SEE_VIBES, "bc_vibes", neon="heart", style=PRIMARY)])
    elif person["photo_id"]:
        keyboard.append([btn(ui.BTN_FIND, "browse", neon="bolt", style=PRIMARY)])
    keyboard.append([btn(ui.BTN_CHANNEL, url=ui.CHANNEL_URL)])
    keyboard.append([btn(ui.BTN_NEWS_OFF, "news_off")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def mark_vote(markup: InlineKeyboardMarkup, chosen: str) -> InlineKeyboardMarkup:
    """Та же клавиатура, но с отметкой выбранного варианта."""
    rows_ = []
    for row in markup.inline_keyboard:
        new_row = []
        for b in row:
            data = b.callback_data or ""
            if data.startswith("vote:"):
                key = data[5:]
                label = ui.FEATURES.get(key, (b.text, ""))[0]
                b = btn(
                    ("✓ " if key == chosen else "") + label,
                    data,
                    style=SUCCESS if key == chosen else None,
                )
            new_row.append(b)
        rows_.append(new_row)
    return InlineKeyboardMarkup(inline_keyboard=rows_)
