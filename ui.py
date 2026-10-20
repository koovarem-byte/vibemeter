"""Все тексты, эмодзи и подписи кнопок Вайбометра.

Стиль меняется только здесь:
- заголовок: эмодзи + <b>Текст</b> обычным регистром;
- один акцент на сообщение, коротко;
- кнопки парами.

Неоновые эмодзи набора VibemeterNeon работают, если у владельца бота
есть Telegram Premium. Без него Telegram сам показывает запасной
обычный эмодзи — код менять не нужно.
"""

from html import escape


# =========================================================
# ЭМОДЗИ
# =========================================================

# имя: (custom_emoji_id, запасной эмодзи)
NEON = {
    "heart": ("5377645830251522729", "🩷"),    # лайк, взаимный вайб
    "fire": ("5375559326549193583", "🔥"),     # процент вайба
    "bolt": ("5377746852177292569", "⚡"),     # быстрые действия, вопросы
    "crown": ("5375286145154329001", "👑"),    # достижения, статистика
    "diamond": ("5377538692292323573", "💎"),  # редкое совпадение
    "star": ("5375383215710185869", "⭐"),     # возвращение, своё
    "candy": ("5377631863017875753", "🍭"),    # игры
}


def e(name: str) -> str:
    """Неоновый эмодзи в тексте (HTML)."""
    emoji_id, fallback = NEON[name]
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def icon(name: str) -> str:
    """id неонового эмодзи для иконки кнопки."""
    return NEON[name][0]


def title(name: str, text: str) -> str:
    """Заголовок с неоновым эмодзи."""
    return f"{e(name)} <b>{text}</b>"


def plain_title(emoji: str, text: str) -> str:
    """Заголовок с обычным эмодзи (служебные экраны)."""
    return f"{emoji} <b>{text}</b>"


def esc(value) -> str:
    """Пользовательский текст для HTML."""
    if value is None:
        return ""
    return escape(str(value))


# =========================================================
# ГЛАВНОЕ МЕНЮ (reply-кнопки, по тексту ловятся хендлеры)
# =========================================================

MENU_FIND = "⚡ Найти вайб"
MENU_LIKES = "🩷 Мои вайбы"
MENU_PROFILE = "👤 Профиль"
MENU_GAMES = "🍭 Игры"
MENU_STATS = "👑 Статистика"
MENU_SETTINGS = "⚙️ Настройки"
MENU_PLACEHOLDER = "Выбери действие"

# старые подписи — чтобы у тех, у кого осталась старая клавиатура,
# кнопки продолжали работать
MENU_ALIASES = {
    MENU_FIND: {"🔎 Найти вайб"},
    MENU_LIKES: {"💜 Мои вайбы"},
    MENU_PROFILE: {"👤 Мой профиль"},
    MENU_GAMES: {"🎮 Вайб-игры"},
    MENU_STATS: {"📊 Статистика"},
    MENU_SETTINGS: set(),
}


def menu_texts(button: str) -> set[str]:
    return {button} | MENU_ALIASES[button]


CANCEL = "Отменить"
CANCEL_ALIASES = {CANCEL, "❌ Отменить"}


# =========================================================
# ПОДПИСИ INLINE-КНОПОК
# =========================================================

BTN_LIKE = "Лайк"
BTN_SKIP = "Пропустить"
BTN_QUESTION = "Вопрос"
BTN_REPORT = "Пожаловаться"
BTN_WRITE = "Написать"
BTN_NEXT = "Дальше"
BTN_VIEW = "Посмотреть"
BTN_LATER = "Позже"
BTN_ANSWER = "Ответить"
BTN_START_GAME = "Начать"
BTN_ACHIEVEMENTS = "Достижения"
BTN_EDIT = "Изменить анкету"
BTN_SEARCH = "Кого искать"
BTN_BLOCKED = "Заблокированные"
BTN_DELETE = "Удалить профиль"
BTN_DELETE_YES = "Да, удалить"
BTN_BACK = "Назад"
BTN_ACCEPT = "Мне есть 18, принимаю"
BTN_POLICY = "Политика"
BTN_MALE = "Парень"
BTN_FEMALE = "Девушка"
BTN_SEARCH_MALE = "Парней"
BTN_SEARCH_FEMALE = "Девушек"
BTN_SEARCH_ALL = "Всех"
BTN_HIDE = "Просто скрыть"
BTN_BAN = "Забанить"
BTN_DISMISS = "Отклонить"

REPORT_REASONS = {
    "fake": "Фейк или спам",
    "rude": "Оскорбления",
    "nsfw": "Неприемлемый контент",
    "minor": "Похоже, младше 18",
    "other": "Другое",
}


# =========================================================
# СОГЛАСИЕ И ПОЛИТИКА
# =========================================================

CONSENT = (
    f"{title('heart', 'Вайбометр')}\n\n"
    "Знакомства по вайбу: сначала интересы и общение, "
    "фото — только после взаимной симпатии.\n\n"
    "• только 18+\n"
    "• анкету видят другие, фото и Telegram — только при взаимном вайбе\n"
    "• удалить всё можно в любой момент в настройках\n\n"
    "Нажимая кнопку, ты подтверждаешь, что тебе есть 18, "
    "и принимаешь /privacy."
)

PRIVACY = (
    f"{plain_title('📄', 'Политика конфиденциальности')}\n\n"
    "<b>Что храним:</b> Telegram ID и username, имя, возраст, пол, "
    "город, интересы, текст «о себе», фото, кого ты ищешь; "
    "лайки, пропуски, блокировки, жалобы, вопросы и ответы, "
    "ответы в играх.\n\n"
    "<b>Зачем:</b> чтобы подбирать анкеты, считать процент вайба "
    "и соединять людей после взаимного лайка. "
    "Данные не продаём и не передаём третьим лицам.\n\n"
    "<b>Кто видит:</b> другие пользователи видят анкету без фото. "
    "Фото и ссылка на твой Telegram открываются только при "
    "взаимном вайбе. Жалобы на тебя видит администратор.\n\n"
    "<b>Где хранится:</b> в базе данных бота (Neon, PostgreSQL).\n\n"
    "<b>Удаление:</b> Настройки → Удалить профиль — "
    "анкета, фото, лайки, вопросы и игры удаляются.\n\n"
    "<b>Возраст:</b> только 18+. Анкеты младше 18 не сохраняем.\n\n"
    "Вопросы по данным — напиши администратору бота."
)


# =========================================================
# START И МЕНЮ
# =========================================================

WELCOME_BACK = (
    f"{title('star', 'С возвращением')}\n\n"
    "Новые анкеты уже ждут."
)
MAIN_MENU = plain_title("🏠", "Главное меню")
NEED_START = "Напиши /start, чтобы начать."
UNKNOWN = "Не понял. Выбери действие в меню."
CANCELLED = "Отменено."
BANNED = "🚫 Аккаунт заблокирован за нарушение правил Вайбометра."


# =========================================================
# АНКЕТА
# =========================================================

PROFILE_STEPS = 8


def step(n: int, text: str) -> str:
    return f"<b>{n}/{PROFILE_STEPS} · {text}</b>"


ASK_NAME = step(1, "Как тебя зовут?")
ASK_AGE = step(2, "Сколько тебе лет?")
ASK_GENDER = step(3, "Кто ты?")
ASK_CITY = step(4, "Из какого ты города?")
ASK_INTERESTS = (
    step(5, "Твои интересы")
    + "\nЧерез запятую: музыка, кино, баскетбол"
)
ASK_ABOUT = step(6, "Пара слов о себе") + "\nДо 500 символов."
ASK_PHOTO = (
    step(7, "Твоё фото")
    + "\nЕго увидят только после взаимного вайба."
)
ASK_SEARCH = step(8, "Кого показывать?")

PROFILE_CONTINUE = "Продолжим анкету 👇"
PROFILE_RESTART = f"{title('star', 'Закончим анкету')}\n\n{ASK_NAME}"
PROFILE_START = f"Отлично, начнём.\n\n{ASK_NAME}"
EDIT_START = f"{plain_title('✏️', 'Новая анкета')}\n\n{ASK_NAME}"
PROFILE_DONE = (
    f"{title('heart', 'Анкета готова')}\n\n"
    "Жми «Найти вайб» — и вперёд."
)
SEARCH_SAVED = "Готово, поиск обновлён."
SEARCH_CHOOSE = plain_title("⚙️", "Кого показывать в поиске?")

ERR_NAME = "Имя — от 2 до 30 символов. Попробуй ещё раз."
ERR_AGE_FORMAT = "Напиши возраст числом, например 21."
ERR_CITY = "Название города выглядит странно. Попробуй ещё раз."
ERR_INTERESTS = "Напиши хотя бы один интерес."
ERR_ABOUT = "Максимум 500 символов."
ERR_TEXT_ONLY = "Ответь текстом, пожалуйста."
ERR_PHOTO_ONLY = "Нужна именно фотография."
ERR_GENDER_LOST = "Не получилось сохранить пол. Выбери ещё раз:"


def err_age_max(max_age: int) -> str:
    return f"Укажи настоящий возраст, до {max_age}."


UNDER_18 = (
    "Извини, Вайбометр только для тех, кому есть 18. "
    "Твои данные мы не сохранили.\n\n"
    "Будем рады видеть тебя позже 🩷"
)


# =========================================================
# КАРТОЧКИ
# =========================================================

def _name_line(person) -> str:
    line = f"<b>{esc(person['full_name'])}"
    if person["age"]:
        line += f", {person['age']}"
    line += "</b>"
    if person["city"]:
        line += f" · {esc(person['city'])}"
    return line


def profile_card(person, vibe=None, common=None) -> str:
    """Чужая анкета. Акцент — процент вайба."""
    lines = []

    if vibe is not None:
        lines.append(title("fire", f"{vibe}% вайба"))
        if vibe >= 80:
            lines.append(f"{e('diamond')} Редкое совпадение")
        lines.append("")

    lines.append(_name_line(person))

    if common:
        lines.append(f"Общее: {esc(', '.join(common))}")

    if person["interests"]:
        lines.append(f"Интересы: {esc(person['interests'])}")

    if person["description"]:
        lines.append("")
        lines.append(f"<i>{esc(person['description'])}</i>")

    return "\n".join(lines)


def search_card(person, vibe, common) -> str:
    return (
        profile_card(person, vibe=vibe, common=common)
        + "\n\n🔒 Фото откроется после взаимного вайба"
    )


def own_profile(user) -> str:
    lines = [title("star", "Твоя анкета"), "", _name_line(user)]

    if user["interests"]:
        lines.append(f"Интересы: {esc(user['interests'])}")

    if user["description"]:
        lines.append("")
        lines.append(f"<i>{esc(user['description'])}</i>")

    return "\n".join(lines)


NO_CANDIDATES = (
    f"{title('bolt', 'Анкеты закончились')}\n\n"
    "Загляни позже — новые люди появляются каждый день."
)


# =========================================================
# ЛАЙКИ И ВЗАИМНОСТЬ
# =========================================================

TOAST_LIKE = "Вайб отправлен"
TOAST_SKIP = "Пропущено"
TOAST_HIDDEN = "Больше не покажем"
TOAST_MUTUAL = "Это взаимно!"
TOAST_SELF = "Это твоя анкета."

LIKED_YOU = (
    f"{title('heart', 'Тебя оценили')}\n\n"
    "Кто-то поймал твой вайб. Загляни — вдруг это взаимно."
)

NO_LIKES = (
    f"{title('heart', 'Пока тихо')}\n\n"
    "Лайкай анкеты — взаимность начинается с тебя."
)


def likes_header(count: int) -> str:
    return title("heart", f"Тебя выбрали: {count}")


def mutual_caption(other) -> str:
    return (
        f"{title('heart', 'Взаимный вайб')}\n\n"
        f"Ты и {_name_line(other)} выбрали друг друга."
    )


def mutual_no_username(other) -> str:
    return (
        f"У {esc(other['full_name'])} нет username в Telegram, "
        "поэтому ссылку на чат дать не можем. "
        "Задай вопрос через анкету — ответ придёт сюда."
    )


CONTACT_LOCKED = "Контакт откроется после взаимного вайба."
USER_NOT_FOUND = "Пользователь не найден."


def contact_text(username: str) -> str:
    return f"{title('heart', 'Пиши первым')}\n\n@{esc(username)}"


# =========================================================
# ВОПРОСЫ
# =========================================================

ASK_QUESTION = (
    f"{title('bolt', 'Твой вопрос')}\n\n"
    "Напиши его одним сообщением — человек увидит текст "
    "и сможет ответить."
)
QUESTION_SENT = "Вопрос отправлен. Ответ пришлю сюда."
QUESTION_FAILED = "Не удалось доставить вопрос — похоже, человек остановил бота."
QUESTION_BAD_LEN = "Вопрос — от 1 до 500 символов."
QUESTION_NO_COMMANDS = "Сначала отправь вопрос или нажми «Отменить»."
QUESTION_NO_TARGET = "Не понял, кому вопрос. Открой анкету ещё раз."
QUESTION_SELF = "Себе вопрос не задать 🙂"
QUESTION_NOT_FOUND = "Вопрос не найден."
QUESTION_ALREADY = "Ты уже ответил на этот вопрос."
ASK_REPLY = "Напиши ответ одним сообщением."
REPLY_SENT = "Ответ отправлен."
REPLY_FAILED = "Не удалось отправить ответ — возможно, ты уже отвечал."


def incoming_question(text: str) -> str:
    return f"{title('bolt', 'Тебе задали вопрос')}\n\n«{esc(text)}»"


def question_answered(question: str, answer: str) -> str:
    return (
        f"{title('bolt', 'Тебе ответили')}\n\n"
        f"Вопрос: «{esc(question)}»\n"
        f"Ответ: «{esc(answer)}»"
    )


# =========================================================
# ЖАЛОБЫ И БАН
# =========================================================

REPORT_ASK = (
    f"{plain_title('⚠️', 'Что не так?')}\n\n"
    "После жалобы эта анкета тебе больше не попадётся."
)
REPORT_SENT = "Спасибо, проверим. Анкету скрыли."
TOAST_REPORT = "Жалоба отправлена"


def admin_report(reason, from_user, person, total, card) -> str:
    username = (
        f" (@{esc(person['username'])})" if person["username"] else ""
    )
    return (
        f"{plain_title('⚠️', 'Новая жалоба')}\n\n"
        f"Причина: <b>{esc(reason)}</b>\n"
        f"От: <code>{from_user}</code>\n"
        f"На: <code>{person['telegram_id']}</code>{username}\n"
        f"Всего жалоб: <b>{total}</b>\n\n"
        f"{card}"
    )


# =========================================================
# СТАТИСТИКА И ДОСТИЖЕНИЯ
# =========================================================

def stats(s) -> str:
    return (
        f"{title('crown', 'Твоя статистика')}\n\n"
        f"Лайков поставлено: {s['likes_sent']}\n"
        f"Тебя выбрали: {s['likes_received']}\n"
        f"Взаимных вайбов: <b>{s['mutual_likes']}</b>\n"
        f"Вопросов: задано {s['questions_sent']} · "
        f"получено {s['questions_received']}\n"
        f"Игр сыграно: {s['games']}"
    )


def achievements(items) -> str:
    """items: [(название, получено)]"""
    return f"{title('crown', 'Достижения')}\n\n" + "\n".join(
        f"{'✅' if done else '🔒'} {name}" for name, done in items
    )


# =========================================================
# НАСТРОЙКИ
# =========================================================

SETTINGS = plain_title("⚙️", "Настройки")
DELETE_ASK = (
    f"{plain_title('⚠️', 'Удалить профиль?')}\n\n"
    "Анкета, фото, лайки, вопросы и игры удалятся без возврата."
)
DELETED = "Профиль удалён. Захочешь вернуться — /start."
DELETE_FAILED = "Не удалось удалить профиль, попробуй позже."
BLOCKED_EMPTY = f"{plain_title('🚫', 'Заблокированные')}\n\nСписок пуст."


def blocked_list(people) -> str:
    lines = [plain_title("🚫", "Заблокированные"), ""]
    for p in people:
        age = p["age"] or "—"
        city = esc(p["city"]) if p["city"] else "—"
        lines.append(f"• {esc(p['full_name'] or 'Без имени')}, {age} · {city}")
    return "\n".join(lines)


# =========================================================
# ИГРЫ
# =========================================================

GAME_NEED_PROFILE = "Сначала заполни анкету: /start"
GAME_WAITING = (
    f"{title('candy', 'Вайб-игра')}\n\n"
    "Ищем второго игрока. Как только найдём — пришлю приглашение."
)
GAME_FOUND = (
    f"{title('candy', 'Соперник найден')}\n\n"
    "5 вопросов «что выберешь?». В конце — процент совпадения."
)
GAME_NOT_FOUND = "Игра не найдена или ты уже ответил на все вопросы."
GAME_ANSWER_REJECTED = "Ответ не принят: вопрос уже отвечен или игра закрыта."
TOAST_ANSWER = "Принято"
GAME_WAIT_OTHER = (
    f"{title('candy', 'Твои ответы готовы')}\n\n"
    "Ждём второго игрока — результат придёт сюда."
)


def game_question(index: int, text: str) -> str:
    return f"{title('candy', f'Вопрос {index + 1}/5')}\n\n{esc(text)}"


def game_result(matches: int, percentage: int) -> str:
    if percentage >= 80:
        verdict = f"{e('diamond')} Редкое совпадение"
    elif percentage >= 60:
        verdict = "Хороший общий вайб"
    elif percentage >= 40:
        verdict = "Кое-что общее есть"
    else:
        verdict = "Вы довольно разные — тоже интересно"

    return (
        f"{title('fire', f'{percentage}% совпадения')}\n\n"
        f"Совпало {matches} из 5. {verdict}."
    )


# =========================================================
# АДМИН
# =========================================================

def admin_stats(s) -> str:
    return (
        f"{plain_title('🛠', 'Вайбометр · админ')}\n\n"
        f"Пользователей: <b>{s['total_users']}</b> (+{s['today']} сегодня)\n"
        f"Анкет: {s['profiles']} · с фото: {s['photos']}\n"
        f"Лайков: {s['likes']} · взаимных: {s['mutual']}\n"
        f"Пропусков: {s['skips']}\n"
        f"Вопросов: {s['questions']} · игр: {s['games']}"
    )


ADMIN_BAN_FORMAT = "Формат: /ban ID или /unban ID"


def admin_banned(person_id: int) -> str:
    return f"🚫 <code>{person_id}</code> забанен. Снять: /unban {person_id}"


def admin_unbanned(person_id: int) -> str:
    return f"✅ <code>{person_id}</code> разбанен."


ADMIN_USER_GONE = "Пользователь не найден или уже удалён."
ADMIN_DISMISSED = "Жалобы отклонены"
