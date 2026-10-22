"""Все тексты, эмодзи и подписи кнопок Вайбометра.

Стиль меняется только здесь:
- заголовок: эмодзи + <b>Текст</b> обычным регистром;
- живой разговорный тон, без точки в конце сообщения;
- у строк анкеты свои иконки (📍 🎯 💬);
- кнопки парами.

Неоновые эмодзи набора VibemeterNeon работают, если у владельца бота
есть Telegram Premium. Без него Telegram сам показывает запасной
обычный эмодзи, код менять не нужно.
"""

from html import escape


# =========================================================
# ЭМОДЗИ
# =========================================================

# имя: (custom_emoji_id, запасной эмодзи)
NEON = {
    "heart": ("5377645830251522729", "🩷"),    # лайк, взаимный вайб
    "fire": ("5375559326549193583", "🔥"),     # процент вайба, серия
    "bolt": ("5377746852177292569", "⚡"),     # быстрые действия, вопросы
    "crown": ("5375286145154329001", "👑"),    # достижения, статистика
    "diamond": ("5377538692292323573", "💎"),  # редкое
    "star": ("5375383215710185869", "⭐"),     # своё, возвращение
    "candy": ("5377631863017875753", "🍭"),    # игры
    "eye": ("5391254726186677649", "👀"),      # тебя выбрали, просмотры
    "trophy": ("5393164242876670090", "🏆"),   # победы, высшее достижение
    "pencil": ("5391094644165619750", "✏️"),   # редактирование
    "speed": ("5391035472401182432", "💨"),    # «Дальше»
    "hands": ("5391048713785360965", "🙌"),    # взаимный вайб
    "car": ("5391075621755468408", "🚘"),      # про запас
    "scroll": ("5393273798902457402", "📜"),   # политика, правила
    "globe": ("5391026517394370172", "🌐"),    # про запас: город, ссылки
    "bolt2": ("5391274195273426031", "⚡"),    # про запас
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


def plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n) % 100
    if 11 <= n <= 19:
        return many
    n %= 10
    if n == 1:
        return one
    if 2 <= n <= 4:
        return few
    return many


def days(n: int) -> str:
    return f"{n} {plural(n, 'день', 'дня', 'дней')}"


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

# старые подписи, чтобы кнопки из старой клавиатуры продолжали работать
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
BTN_SKIP = "Дальше"
BTN_QUESTION = "Спросить"
BTN_REPORT = "Пожаловаться"
BTN_WRITE = "Написать"
BTN_NEXT = "Дальше"
BTN_VIEW = "Посмотреть"
BTN_LATER = "Позже"
BTN_ANSWER = "Ответить"
BTN_START_GAME = "Начать"
BTN_PLAY_AGAIN = "Сыграть ещё"
BTN_OPEN_APP = "✨ Открыть Вайбометр"
BTN_ACHIEVEMENTS = "Зал славы"
BTN_EDIT = "Изменить анкету"
BTN_SEARCH = "Кого искать"
BTN_BLOCKED = "Заблокированные"
BTN_DELETE = "Удалить профиль"
BTN_DELETE_YES = "Да, удалить"
BTN_BACK = "Назад"
BTN_ACCEPT = "Мне есть 18, поехали"
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
    f"{title('heart', 'Привет, я Вайбометр')}\n\n"
    "Тут сначала знакомятся по вайбу: интересы, характер, общие темы. "
    "Фото открывается, только когда вы оба лайкнули друг друга. "
    "Без оценок по внешности\n\n"
    "🔞 Только 18+\n"
    "🗑 Профиль можно удалить в любой момент\n\n"
    "Согласен с /privacy и тебе есть 18? Поехали"
)

PRIVACY = (
    f"{title('scroll', 'Политика конфиденциальности')}\n\n"
    "<b>Что храним:</b> Telegram ID и username, имя, возраст, пол, "
    "город, интересы, текст о себе, фото, кого ты ищешь; "
    "лайки, пропуски, блокировки, жалобы, вопросы и ответы, "
    "ответы в играх, дни активности для серии\n\n"
    "<b>Зачем:</b> чтобы подбирать анкеты, считать процент вайба "
    "и соединять людей после взаимного лайка. "
    "Данные не продаём и третьим лицам не передаём\n\n"
    "<b>Кто видит:</b> другие пользователи видят анкету без фото. "
    "Фото и ссылка на твой Telegram открываются только при "
    "взаимном вайбе. Жалобы на тебя видит администратор\n\n"
    "<b>Где хранится:</b> в базе данных бота (Neon, PostgreSQL)\n\n"
    "<b>Удаление:</b> Настройки → Удалить профиль. "
    "Анкета, фото, лайки, вопросы и игры удаляются\n\n"
    "<b>Возраст:</b> только 18+, анкеты младше 18 не сохраняем\n\n"
    "Вопросы по данным можно задать администратору бота"
)


# =========================================================
# START И МЕНЮ
# =========================================================

def welcome_back(streak: int) -> str:
    text = f"{title('star', 'С возвращением')}\n\nНовые анкеты уже ждут"
    if streak >= 2:
        text += f"\n{e('fire')} Серия {days(streak)}"
    return text


MAIN_MENU = plain_title("🏠", "Главное меню")
NEED_START = "Напиши /start, и начнём"
UNKNOWN = "Не понял 🙂 Выбери что-нибудь в меню"
CANCELLED = "Окей, отменили"
PHOTO_UPDATED = "📸 Новое фото анкеты из Вайбометра"
BANNED = "🚫 Аккаунт заблокирован за нарушение правил Вайбометра"


def streak_notice(streak: int) -> str:
    return f"{e('fire')} Серия {days(streak)} подряд! Загляни завтра, чтобы не сгорела"


# =========================================================
# АНКЕТА
# =========================================================

PROFILE_STEPS = 8


def step(n: int, text: str) -> str:
    return f"<b>{n}/{PROFILE_STEPS} · {text}</b>"


ASK_NAME = step(1, "Как тебя звать?")
ASK_AGE = step(2, "Сколько тебе лет?") + "\nНапиши цифрой"
ASK_GENDER = step(3, "Ты парень или девушка?")
ASK_CITY = step(4, "Из какого ты города?")
ASK_INTERESTS = (
    step(5, "Чем зажигаешься?")
    + "\nПиши как есть: баскетбол, ночные прогулки, старый рэп"
)
ASK_ABOUT = step(6, "Что о тебе стоит знать за 10 секунд?") + "\nДо 500 символов"
ASK_PHOTO = (
    step(7, "Пришли своё фото")
    + "\nОно спрятано, пока вайб не станет взаимным 🔒"
)
ASK_SEARCH = step(8, "Кого тебе показывать?")

PROFILE_CONTINUE = "Продолжим анкету 👇"
PROFILE_RESTART = f"{title('star', 'Давай закончим анкету')}\n\n{ASK_NAME}"
PROFILE_START = f"Супер, начнём 🙌\n\n{ASK_NAME}"
EDIT_START = f"{title('pencil', 'Заполним анкету заново')}\n\n{ASK_NAME}"
PROFILE_DONE = (
    f"{title('heart', 'Готово, ты на радаре')}\n\n"
    "Жми «Найти вайб» и смотри, с кем совпадёшь"
)
SEARCH_SAVED = "Готово, поиск обновили 👌"
SEARCH_CHOOSE = plain_title("⚙️", "Кого показывать в поиске?")

ERR_NAME = "Имя от 2 до 30 символов, давай ещё раз"
ERR_AGE_FORMAT = "Нужна цифра, например 21"
ERR_CITY = "Не похоже на город, попробуй ещё раз"
ERR_INTERESTS = "Хотя бы один интерес, это важно для вайба"
ERR_ABOUT = "Многовато, уложись в 500 символов"
ERR_TEXT_ONLY = "Тут нужен текст"
ERR_PHOTO_ONLY = "Нужна именно фотография 📸"
ERR_GENDER_LOST = "Не получилось сохранить пол, выбери ещё раз:"


def err_age_max(max_age: int) -> str:
    return f"Хм, укажи настоящий возраст, до {max_age}"


UNDER_18 = (
    "Извини, Вайбометр только для тех, кому есть 18. "
    "Данные мы не сохранили\n\n"
    "Возвращайся, когда подрастёшь 🩷"
)


# =========================================================
# КАРТОЧКИ
# =========================================================

def vibe_bar(vibe: int) -> str:
    filled = max(0, min(10, round(vibe / 10)))
    return "▰" * filled + "▱" * (10 - filled)


def _interests(interests: str, common) -> str:
    """Интересы, общие выделены жирным."""
    common = {c.lower() for c in (common or [])}
    items = [i.strip() for i in (interests or "").split(",") if i.strip()]
    return ", ".join(
        f"<b>{esc(i)}</b>" if i.lower() in common else esc(i)
        for i in items
    )


def _name_age(person) -> str:
    text = f"<b>{esc(person['full_name'])}"
    if person["age"]:
        text += f", {person['age']}"
    return text + "</b>"


def profile_card(person, vibe=None, common=None, same_city=False) -> str:
    """Чужая анкета. Акцент на проценте вайба"""
    lines = []

    if vibe is not None:
        lines.append(f"{title('fire', f'{vibe}% вайба')} {vibe_bar(vibe)}")
        if vibe >= 80:
            lines.append(f"{e('diamond')} Редкое совпадение")
        lines.append("")

    lines.append(_name_age(person))

    if person["city"]:
        lines.append(f"📍 {esc(person['city'])}")

    if person["interests"]:
        lines.append(f"🎯 {_interests(person['interests'], common)}")

    if person["description"]:
        lines.append(f"💬 {esc(person['description'])}")

    if common:
        lines.append("")
        lines.append("✨ Вас объединяют: " + esc(", ".join(common)))
    elif same_city:
        lines.append("")
        lines.append("✨ Вы из одного города")

    return "\n".join(lines)


def search_card(person, vibe, common, same_city=False) -> str:
    return (
        profile_card(person, vibe=vibe, common=common, same_city=same_city)
        + "\n🔒 Фото откроется, если вайб взаимный"
    )


def own_profile(user, stats=None, done=0, total=0) -> str:
    lines = [plain_title("👤", "Мой профиль"), ""]
    lines.append(_name_age(user))

    if user["city"]:
        lines.append(f"📍 {esc(user['city'])}")

    if user["interests"]:
        lines += ["", "🎯 <b>Интересы:</b>", esc(user["interests"])]

    if user["description"]:
        lines += ["", "💬 <b>О себе:</b>", esc(user["description"])]

    if stats is not None:
        lines += [
            "",
            f"{e('fire')} Серия {days(stats['streak_days'])} · "
            f"{e('crown')} Уровень {level(done, total)[0]} · "
            f"{level(done, total)[1]} · {done} из {total} достижений",
        ]

    return "\n".join(lines)


NO_CANDIDATES = (
    f"{title('bolt', 'Пока всех посмотрел')}\n\n"
    "Загляни позже: новые люди появляются каждый день, и вайб тоже"
)


# =========================================================
# ЛАЙКИ И ВЗАИМНОСТЬ
# =========================================================

TOAST_LIKE = "Вайб отправлен 🩷"
TOAST_SKIP = "Окей, дальше"
TOAST_HIDDEN = "Больше не покажем"
TOAST_MUTUAL = "Это взаимно!"
TOAST_SELF = "Это твоя анкета 🙂"

LIKED_YOU = (
    f"{title('heart', 'Тебя лайкнули')}\n\n"
    "Кто-то поймал твой вайб. Загляни, вдруг это взаимно"
)

NO_LIKES = (
    f"{title('heart', 'Пока тихо')}\n\n"
    "Пока никто не откликнулся. Лайкни 3–5 анкет, и первые совпадения появятся быстрее"
)


def likes_header(count: int) -> str:
    who = plural(count, "человек", "человека", "человек")
    return title("eye", f"Тебя выбрали {count} {who}")


def mention(person) -> str:
    """Имя-ссылка на профиль: работает и без username"""
    return (
        f'<a href="tg://user?id={person["telegram_id"]}">'
        f"{esc(person['full_name'])}</a>"
    )


def mutual_caption(other) -> str:
    line = esc(other["full_name"])
    if other["age"]:
        line += f", {other['age']}"
    if other["city"]:
        line += f", {esc(other['city'])}"

    return (
        f"{title('hands', 'Взаимный вайб. Вот как он выглядит')}\n"
        f"{line}\n\n"
        f"Начинай общаться 👉 {mention(other)}"
    )


def mutual_no_username(other) -> str:
    return (
        f"Начинай общаться 👉 {mention(other)}\n\n"
        "Если ссылка не открывается, значит человек закрыл профиль "
        "настройками приватности. Тогда задай вопрос через анкету"
    )


CONTACT_LOCKED = "Контакт откроется после взаимного вайба"
USER_NOT_FOUND = "Пользователь не найден"


def contact_text(username: str) -> str:
    return f"{title('heart', 'Пиши первым!')}\n\n@{esc(username)}"


# =========================================================
# ВОПРОСЫ
# =========================================================

ASK_QUESTION = (
    f"{title('bolt', 'Задай вопрос')}\n\n"
    "Напиши его одним сообщением. Человек увидит его и сможет ответить"
)
QUESTION_SENT = "Вопрос ушёл ⚡ Ответ пришлю сюда"
QUESTION_FAILED = "Не получилось доставить вопрос, похоже, человек остановил бота"
QUESTION_BAD_LEN = "Вопрос должен быть от 1 до 500 символов"
QUESTION_NO_COMMANDS = "Сначала отправь вопрос или нажми «Отменить»"
QUESTION_NO_TARGET = "Не понял, кому вопрос, открой анкету ещё раз"
QUESTION_SELF = "Себе вопрос не задать 🙂"
QUESTION_NOT_FOUND = "Вопрос не найден"
QUESTION_ALREADY = "Ты уже ответил на этот вопрос"
ASK_REPLY = "Напиши ответ одним сообщением"
REPLY_SENT = "Ответ отправлен ⚡"
REPLY_FAILED = "Не получилось отправить ответ, возможно, ты уже отвечал"


def incoming_question(text: str) -> str:
    return f"{title('bolt', 'Тебе задали вопрос')}\n\n«{esc(text)}»"


def question_answered(question: str, answer: str) -> str:
    return (
        f"{title('bolt', 'Тебе ответили')}\n\n"
        f"❓ «{esc(question)}»\n"
        f"💬 «{esc(answer)}»"
    )


# =========================================================
# ЖАЛОБЫ И БАН
# =========================================================

REPORT_ASK = (
    f"{plain_title('⚠️', 'Что не так?')}\n\n"
    "После жалобы эта анкета тебе больше не попадётся"
)
REPORT_SENT = "Спасибо, проверим. Анкету скрыли"
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
# СТАТИСТИКА И ЗАЛ СЛАВЫ
# =========================================================

def stats(s) -> str:
    return (
        f"{title('crown', 'Твоя статистика')}\n\n"
        f"{e('fire')} Серия: <b>{days(s['streak_days'])}</b> · "
        f"рекорд {days(s['best_streak'])}\n\n"
        f"{e('heart')} Лайков поставлено: {s['likes_sent']}\n"
        f"{e('eye')} Тебя выбрали: {s['likes_received']}\n"
        f"{e('hands')} Взаимных вайбов: <b>{s['mutual_likes']}</b>\n"
        f"{e('bolt')} Вопросов: задано {s['questions_sent']}, "
        f"получено {s['questions_received']}\n"
        f"{e('candy')} Игр сыграно: {s['games']}"
    )


# (эмодзи, название, описание, ключ статистики, цель)
ACHIEVEMENTS = (
    ("heart", "Первый вайб", "первый лайк", "likes_sent", 1),
    ("diamond", "Взаимность", "первый взаимный вайб", "mutual_likes", 1),
    ("fire", "В огне", "серия 7 дней", "best_streak", 7),
    ("heart", "Сердцеед", "25 лайков", "likes_sent", 25),
    ("trophy", "Легенда", "серия 30 дней", "best_streak", 30),
    ("candy", "Душа компании", "10 игр", "games", 10),
    ("bolt", "Болтун", "10 вопросов", "questions_sent", 10),
    ("star", "Магнит", "тебя выбрали 25 раз", "likes_received", 25),
    ("star", "Лидер вайба", "3 друга по твоей ссылке", "referrals", 3),
)


def achieved(s, achievement) -> bool:
    *_, key, goal = achievement
    return s[key] >= goal


def achievements_progress(s) -> tuple[int, int]:
    done = sum(1 for a in ACHIEVEMENTS if achieved(s, a))
    return done, len(ACHIEVEMENTS)


# Уровни по числу открытых достижений (Mini App показывает те же)
LEVELS = ((0, "Новичок"), (2, "В теме"), (4, "Вайбер"), (6, "Звезда"))


def level(done: int, total: int) -> tuple[int, str, int]:
    """(номер, название, сколько достижений нужно для следующего)."""
    steps = list(LEVELS) + [(total, "Легенда")]
    n, name, next_at = 1, steps[0][1], steps[1][0]
    for i, (at, title_) in enumerate(steps):
        if done >= at:
            n, name = i + 1, title_
            next_at = steps[i + 1][0] if i + 1 < len(steps) else total
    return n, name, next_at


def hall_of_fame(s) -> str:
    done, total = achievements_progress(s)
    n, name, next_at = level(done, total)
    lines = [
        f"{title('crown', 'Зал славы')} · {done} из {total}",
        f"Уровень {n} · <b>{name}</b>"
        + (f" · до следующего {next_at - done}" if next_at > done else ""),
        "",
    ]

    # открытые сверху
    ordered = sorted(ACHIEVEMENTS, key=lambda a: not achieved(s, a))

    for a in ordered:
        emoji, name, hint, *_ = a
        if achieved(s, a):
            lines.append(f"{e(emoji)} <b>{name}</b> · {hint}")
        else:
            lines.append(f"🔒 {name} · {hint}")

    return "\n".join(lines)


# =========================================================
# НАСТРОЙКИ
# =========================================================

SETTINGS = plain_title("⚙️", "Настройки")
DELETE_ASK = (
    f"{plain_title('⚠️', 'Точно удалить профиль?')}\n\n"
    "Анкета, фото, лайки, вопросы и игры удалятся насовсем"
)
DELETED = "Профиль удалён. Захочешь вернуться, просто напиши /start"
DELETE_FAILED = "Не получилось удалить профиль, попробуй чуть позже"
BLOCKED_EMPTY = f"{plain_title('🚫', 'Заблокированные')}\n\nТут пусто, и это хорошо"


def blocked_list(people) -> str:
    lines = [plain_title("🚫", "Заблокированные"), ""]
    for p in people:
        age = p["age"] or "?"
        city = esc(p["city"]) if p["city"] else "город не указан"
        lines.append(f"• {esc(p['full_name'] or 'Без имени')}, {age}, {city}")
    return "\n".join(lines)


# =========================================================
# ИГРЫ
# =========================================================

GAME_NEED_PROFILE = "Сначала заполни анкету: /start"
GAME_OPEN_APP = f"{title('candy', 'Вайб-игра')}\n\nИграем в приложении: ищем пару, 5 быстрых вопросов и процент совпадения 👇"
GAME_FOUND_PING = f"{title('candy', 'Пара для игры найдена!')}\n\nОткрой игру, 5 быстрых вопросов 👇"
GAME_RESULT_PING = f"{title('candy', 'Игра готова')}\n\nСоперник ответил, смотри, насколько вы совпали 👇"
OPEN_APP_HINT = "Всё самое красивое — в приложении: свайпы, шкала вайба, зал славы 👇"
SHARE_CARD_CAPTION = "Сохрани картинку и выложи в сторис 💜\nПусть друзья проверят свой вайб: {link}"
DUO_INVITE = "{name} зовёт тебя сыграть в «{game}» 👇"
DUO_DONE = "Игра «{game}» с {name} закончилась, смотри итог 👇"
DUO_YOUR_TURN = "{name} ждёт твоего хода в «{game}» 👇"
GAME_WAITING = (
    f"{title('candy', 'Вайб-игра')}\n\n"
    "Ищу тебе пару. Как найду, сразу пришлю вопросы"
)
GAME_FOUND = (
    f"{title('candy', 'Пара найдена')}\n\n"
    "5 вопросов «что выберешь?», в конце узнаете, насколько совпали"
)
GAME_NOT_FOUND = "Игра не найдена или ты уже ответил на все вопросы"
GAME_ANSWER_REJECTED = "Ответ не принят: вопрос уже отвечен или игра закрыта"
TOAST_ANSWER = "Принято"
GAME_YOUR_TURN = (
    f"{title('candy', 'Соперник уже ответил')}\n\n"
    "Твоя очередь, жми на варианты ниже"
)
GAME_WAIT_OTHER = (
    f"{title('candy', 'Твои ответы готовы')}\n\n"
    "Ждём второго игрока, результат придёт сюда"
)


def game_question(index: int, text: str) -> str:
    return f"{title('candy', f'Вопрос {index + 1} из 5')}\n\n{esc(text)}"


def game_result(matches: int, percentage: int) -> str:
    if percentage >= 80:
        verdict = f"{e('diamond')} Редкое совпадение!"
    elif percentage >= 60:
        verdict = "Хороший общий вайб 🙌"
    elif percentage >= 40:
        verdict = "Кое-что общее точно есть"
    else:
        verdict = "Вы довольно разные, и это тоже интересно"

    return (
        f"{title('fire', f'{percentage}% совпадения')} {vibe_bar(percentage)}\n\n"
        f"Совпали в {matches} вопросах из 5\n{verdict}"
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
    return f"🚫 <code>{person_id}</code> забанен, снять: /unban {person_id}"


def admin_unbanned(person_id: int) -> str:
    return f"✅ <code>{person_id}</code> разбанен"


ADMIN_USER_GONE = "Пользователь не найден или уже удалён"
ADMIN_DISMISSED = "Жалобы отклонены"


def _bar(value: int, goal: int, width: int = 8) -> str:
    filled = round(min(value, goal) / goal * width) if goal else width
    return "▰" * filled + "▱" * (width - filled)


def stats_full(s) -> str:
    """Статистика и Зал славы в одном сообщении."""
    done, total = achievements_progress(s)
    n, name, next_at = level(done, total)
    lines = [
        stats(s),
        "",
        f"{title('crown', 'Зал славы')} · {done} из {total}",
        f"Уровень {n} · <b>{name}</b>"
        + (f" · до следующего {next_at - done}" if next_at > done else ""),
        "",
    ]
    for a in sorted(ACHIEVEMENTS, key=lambda a: not achieved(s, a)):
        emoji, ach_name, hint, key, goal = a
        if achieved(s, a):
            lines.append(f"{e(emoji)} <b>{ach_name}</b> · {hint}")
        else:
            lines.append(
                f"🔒 {ach_name} · {hint}\n"
                f"      {_bar(s[key], goal)} {min(s[key], goal)}/{goal}"
            )
    return "\n".join(lines)
