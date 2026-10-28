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

import vip


# =========================================================
# ЭМОДЗИ
# =========================================================

# имя: (custom_emoji_id, запасной эмодзи)
NEON = {
    "heart": ("5377645830251522729", "💜"),    # вайб (лайк), взаимный вайб
    "fire": ("5375559326549193583", "🔥"),     # процент вайба, серия
    "bolt": ("5377746852177292569", "⚡"),     # быстрые действия, вопросы
    "crown": ("5375286145154329001", "👑"),    # достижения, статистика
    "diamond": ("5377538692292323573", "💎"),  # редкое
    "star": ("5375383215710185869", "⭐"),     # своё, возвращение
    "candy": ("5377631863017875753", "🍭"),    # игры
    "spark": ("5391274195273426031", "⚡"),    # искры: «вас объединяют»
    "eye": ("5391254726186677649", "👀"),      # тебя выбрали
    "trophy": ("5393164242876670090", "🏆"),   # победы, высшее достижение
    "gamepad": ("5391094644165619750", "🎮"),  # игры
    "chat": ("5391035472401182432", "💬"),     # вопросы, общение
    "hands": ("5391048713785360965", "🙌"),    # взаимный вайб
    "speedo": ("5391075621755468408", "⏱"),    # спидометр: «Дальше»
    "lock": ("5393273798902457402", "🔒"),     # закрытое фото, приватность
    "gear": ("5391026517394370172", "⚙️"),     # настройки
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

# Кнопки меню без эмодзи в тексте: иконку даёт MENU_ICONS (неон).
MENU_FIND = "Найти вайб"
MENU_LIKES = "Мои вайбы"
MENU_PROFILE = "Профиль"
MENU_GAMES = "Игры"
MENU_STATS = "Статистика"
MENU_SETTINGS = "Настройки"

MENU_ICONS = {
    MENU_FIND: "bolt",
    MENU_LIKES: "heart",
    MENU_PROFILE: "star",
    MENU_GAMES: "gamepad",
    MENU_STATS: "crown",
    MENU_SETTINGS: "gear",
}
MENU_PLACEHOLDER = "Выбери действие"

# старые подписи, чтобы кнопки из старой клавиатуры продолжали работать
MENU_ALIASES = {
    # старые подписи: у кого-то ещё висит прежняя клавиатура
    MENU_FIND: {"🔎 Найти вайб", "⚡ Найти вайб"},
    MENU_LIKES: {"💜 Мои вайбы", "🩷 Мои вайбы"},
    MENU_PROFILE: {"👤 Мой профиль", "👤 Профиль"},
    MENU_GAMES: {"🎮 Вайб-игры", "🍭 Игры"},
    MENU_STATS: {"📊 Статистика", "👑 Статистика"},
    MENU_SETTINGS: {"⚙️ Настройки"},
}


def menu_texts(button: str) -> set[str]:
    return {button} | MENU_ALIASES[button]


# Нижнее меню в ленте (вместо главного, пока листаешь анкеты)
BROWSE_LIKE = "Вайб"
BROWSE_SKIP = "Дальше"
BROWSE_ASK = "Спросить"
BROWSE_REPORT = "Пожаловаться"
BROWSE_MENU = "Меню"
BROWSE_ICONS = {
    BROWSE_LIKE: "heart",
    BROWSE_SKIP: "speedo",
    BROWSE_ASK: "chat",
    BROWSE_MENU: "star",
}
BROWSE_PLACEHOLDER = "Вайб или дальше?"


def menu_home(incoming: int) -> str:
    """Возврат из ленты в главное меню."""
    text = MAIN_MENU
    if incoming:
        text += (
            f"\n\n{e('eye')} Тебя ждут <b>{incoming}</b> "
            f"{plural(incoming, 'вайб', 'вайба', 'вайбов')} — загляни в «Мои вайбы»"
        )
    return text


CANCEL = "Отменить"
CANCEL_ALIASES = {CANCEL, "❌ Отменить"}


# =========================================================
# ПОДПИСИ INLINE-КНОПОК
# =========================================================

BTN_LIKE = "Вайб"
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
BTN_STORY = "Картинка для сторис"
BTN_PLAY_TOGETHER = "Сыграть вместе"
BTN_OPEN_APP = "Открыть Вайбометр"
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
    "Фото открывается, только когда вы оба отправили друг другу вайб. "
    "Без оценок по внешности\n\n"
    "🔞 Только 18+\n"
    "🤳 Только своё фото с лицом\n"
    "🗑 Профиль можно удалить в любой момент\n\n"
    "Согласен с /privacy и тебе есть 18? Поехали"
)

PRIVACY = (
    f"{title('lock', 'Политика конфиденциальности')}\n\n"
    "<b>Что храним:</b> Telegram ID и username, имя, возраст, пол, "
    "город, интересы, текст о себе, фото, кого ты ищешь; "
    "лайки, пропуски, блокировки, жалобы, вопросы и ответы, "
    "ответы в играх и тестах, дни активности для серии и статистики, "
    "голос за новые функции, "
    "@username, которые ты отметил в «Тайной симпатии» (их никто не видит)\n\n"
    "<b>Зачем:</b> чтобы подбирать анкеты, считать процент вайба "
    "и соединять людей после взаимного лайка. "
    "Данные не продаём и третьим лицам не передаём\n\n"
    "<b>Кто видит:</b> другие пользователи видят анкету без фото. "
    "Фото и ссылка на твой Telegram открываются только при "
    "взаимном вайбе. Жалобы на тебя видит администратор\n\n"
    "<b>Где хранится:</b> в базе данных бота (Neon, PostgreSQL)\n\n"
    "<b>Удаление:</b> Настройки → Удалить профиль. "
    "Анкета, фото, лайки, вопросы, игры, тесты и тайные симпатии удаляются\n\n"
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
PHOTO_RULE = "Только своё фото, где видно лицо. Чужое или без лица — анкету скроем"

ASK_PHOTO = (
    step(7, "Пришли своё фото")
    + f"\nОно спрятано, пока вайб не станет взаимным {e('lock')}\n\n"
    + PHOTO_RULE
)
ASK_SEARCH = step(8, "Кого тебе показывать?")

PROFILE_CONTINUE = "Продолжим анкету 👇"
PROFILE_RESTART = f"{title('star', 'Давай закончим анкету')}\n\n{ASK_NAME}"
PROFILE_START = f"Супер, начнём {e('hands')}\n\n{ASK_NAME}"
EDIT_START = f"{title('gear', 'Заполним анкету заново')}\n\n{ASK_NAME}"
PROFILE_DONE = (
    f"{title('heart', 'Готово, ты на радаре')}\n\n"
    "Жми «Найти вайб» и смотри, с кем совпадёшь"
)
SEARCH_SAVED = "Готово, поиск обновили 👌"
SEARCH_CHOOSE = title("gear", "Кого показывать в поиске?")

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
    f"Возвращайся, когда подрастёшь {e('heart')}"
)


# =========================================================
# КАРТОЧКИ
# =========================================================

def vibe_bar(vibe: int) -> str:
    filled = max(0, min(10, round(vibe / 10)))
    return "▰" * filled + "▱" * (10 - filled)


def _interests(interests: str, common) -> str:
    """Интересы через точку, общие выделены жирным."""
    common = {c.lower() for c in (common or [])}
    items = [i.strip() for i in (interests or "").split(",") if i.strip()]
    return " · ".join(
        f"<b>{esc(i)}</b>" if i.lower() in common else esc(i)
        for i in items
    )


def _about(text: str) -> str:
    """«О себе» цитатой: отделяется полосой, длинное сворачивается."""
    tag = "<blockquote expandable>" if len(text) > 160 else "<blockquote>"
    return f"{tag}{esc(text)}</blockquote>"


VIP_BADGE = "💎"


def _badge(person) -> str:
    return f" {VIP_BADGE}" if vip.is_vip(person) else ""


def _name_age(person) -> str:
    text = f"<b>{esc(person['full_name'])}"
    if person["age"]:
        text += f", {person['age']}"
    return text + "</b>" + _badge(person)


def profile_card(person, vibe=None, common=None, same_city=False) -> str:
    """Чужая анкета: имя, вайб, интересы, «о себе» — отдельными блоками"""
    blocks = []

    head = _name_age(person)
    if person["city"]:
        head += f"\n📍 {esc(person['city'])}"
    blocks.append(head)

    if vibe is not None:
        line = f"{e('fire')} <b>{vibe}% вайба</b>"
        if vibe >= 80:
            line += f" · {e('diamond')} редкое совпадение"
        blocks.append(f"{line}\n{vibe_bar(vibe)}")

    if person["interests"]:
        blocks.append(f"🎯 {_interests(person['interests'], common)}")

    if person["description"]:
        blocks.append(_about(person["description"]))

    if common:
        blocks.append(f"{e('spark')} Вас объединяет: " + esc(", ".join(common)))
    elif same_city:
        blocks.append(f"{e('spark')} Вы из одного города")

    return "\n\n".join(blocks)


def search_card(person, vibe, common, same_city=False, liked_me=False) -> str:
    text = profile_card(person, vibe=vibe, common=common, same_city=same_city)
    if liked_me:
        # из «Мои вайбы»: человек уже выбрал тебя — один вайб, и взаимно
        return text + f"\n\n{e('eye')} <b>Ты уже нравишься этому человеку</b>\nОтправь вайб — и откроются фото и чат"
    return text + f"\n\n{e('lock')} <i>Фото откроется, если вайб взаимный</i>"


def own_profile(user, stats=None, done=0, total=0, city=None) -> str:
    blocks = [plain_title("👤", "Мой профиль")]

    head = _name_age(user)
    if user["city"]:
        head += f"\n📍 {esc(user['city'])}"
    blocks.append(head)

    if user["interests"]:
        blocks.append(f"🎯 {_interests(user['interests'], None)}")

    if user["description"]:
        blocks.append(_about(user["description"]))

    if stats is not None:
        lvl_n, lvl_name = level(done, total)[:2]
        blocks.append(
            f"{e('fire')} Серия {days(stats['streak_days'])}\n"
            f"{e('crown')} Уровень {lvl_n} · {lvl_name} · {done} из {total} достижений"
        )

    if vip.is_vip(user):
        blocks.append(vip_status(user))

    if city:
        blocks.append(f"{city_progress(city)}\nЗови друзей: каждый двигает шкалу города")

    return "\n\n".join(blocks)


NO_CANDIDATES = (
    f"{title('bolt', 'Пока всех посмотрел')}\n\n"
    "Загляни позже: новые люди появляются каждый день, и вайб тоже"
)


# =========================================================
# ЛАЙКИ И ВЗАИМНОСТЬ
# =========================================================

TOAST_LIKE = "Вайб отправлен 💜"
TOAST_SKIP = "Окей, дальше"
TOAST_HIDDEN = "Больше не покажем"
TOAST_MUTUAL = "Это взаимно!"
TOAST_SELF = "Это твоя анкета 🙂"

LIKED_YOU = (
    f"{title('heart', 'Тебе отправили вайб')}\n\n"
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
    line += _badge(other)

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
    f"{title('chat', 'Задай вопрос')}\n\n"
    "Напиши его одним сообщением. Имя и фото не покажем: человек увидит "
    "только твой возраст, город и общие интересы\n\n"
    "Мат, пошлость и оскорбления не пропускаем"
)
BTN_VIBE_BACK = "Вайб в ответ"
NOT_SENT = "🚫 Такое не отправлю — перепиши по-человечески"
Q_REPORTED = "Спасибо, проверим. Этот человек тебе больше не напишет"
Q_LIKED = "Вайб ушёл. Если он взаимный — откроются имя и фото"
QUESTION_SENT = f"Вопрос ушёл {e('bolt')} Ответ пришлю сюда"
QUESTION_FAILED = "Не получилось доставить вопрос, похоже, человек остановил бота"
QUESTION_BAD_LEN = "Вопрос должен быть от 1 до 500 символов"
QUESTION_NO_COMMANDS = "Сначала отправь вопрос или нажми «Отменить»"
QUESTION_NO_TARGET = "Не понял, кому вопрос, открой анкету ещё раз"
QUESTION_SELF = "Себе вопрос не задать 🙂"
QUESTION_NOT_FOUND = "Вопрос не найден"
QUESTION_ALREADY = "Ты уже ответил на этот вопрос"
ASK_REPLY = "Напиши ответ одним сообщением"
REPLY_SENT = f"Ответ отправлен {e('bolt')}"
REPLY_FAILED = "Не получилось отправить ответ, возможно, ты уже отвечал"


GENDER_WORD = {"female": "девушка", "male": "парень"}


def incoming_question(text: str, asker=None, vibe=None, common=()) -> str:
    lines = [title("chat", "Тебе задали вопрос"), "", f"«{esc(text)}»"]
    if asker:
        who = ", ".join(x for x in (
            GENDER_WORD.get(asker.get("gender") or "", ""),
            str(asker["age"]) if asker.get("age") else "",
            esc((asker.get("city") or "").strip()),
        ) if x)
        lines += ["", f"Спросил(а): {who}"]
        if common:
            lines.append(f"{e('spark')} Общее: {esc(' · '.join(common))}")
        if vibe is not None:
            lines.append(f"{e('fire')} Вайб {vibe}%")
        lines += ["", "Понравился вопрос — отправь вайб в ответ. Имя и фото откроются, если вайб взаимный"]
    return "\n".join(lines)


def question_answered(question: str, answer: str) -> str:
    return (
        f"{title('chat', 'Тебе ответили')}\n\n"
        f"❓ «{esc(question)}»\n"
        f"{e('chat')} «{esc(answer)}»"
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
        f"{e('chat')} Вопросов: задано {s['questions_sent']}, "
        f"получено {s['questions_received']}\n"
        f"{e('gamepad')} Игр сыграно: {s['games']}"
    )


# (эмодзи, название, описание, ключ статистики, цель)
ACHIEVEMENTS = (
    ("heart", "Первый вайб", "отправь первый вайб", "likes_sent", 1),
    ("diamond", "Взаимность", "первый взаимный вайб", "mutual_likes", 1),
    ("fire", "В огне", "серия 7 дней", "best_streak", 7),
    ("heart", "Сердцеед", "25 вайбов", "likes_sent", 25),
    ("trophy", "Легенда", "серия 30 дней", "best_streak", 30),
    ("gamepad", "Душа компании", "10 игр", "games", 10),
    ("chat", "Болтун", "10 вопросов", "questions_sent", 10),
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
            lines.append(f"{e('lock')} {name} · {hint}")

    return "\n".join(lines)


# =========================================================
# НАСТРОЙКИ
# =========================================================

SETTINGS = title("gear", "Настройки")
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
SHARE_CARD_CAPTION = f"Сохрани картинку и выложи в сторис {e('heart')}\nПусть друзья проверят свой вайб: {{link}}"

NEED_PROFILE = "Сначала заполни анкету: напиши /start, это минута"

TOO_FAST = "Слишком быстро, секунду"
TOO_FAST_LIKES = "Много вайбов за час. Передохни немного и возвращайся"
TOO_FAST_QUESTIONS = "Много вопросов за час. Подожди немного, потом спросишь ещё"

def city_progress(city: dict) -> str:
    """«Псков: 37 из 100» со шкалой."""
    filled = max(0, min(10, city["count"] * 10 // city["goal"]))
    return (
        f"{e('fire')} <b>{esc(city['name'])}: {city['count']} из {city['goal']}</b>\n"
        f"{'▰' * filled}{'▱' * (10 - filled)}"
    )


def friend_joined(total: int, city: dict | None) -> str:
    text = (
        f"{title('star', 'Твой друг в Вайбометре')}\n\n"
        f"Приглашено: {total}. В награду твоя анкета сутки показывается "
        "другим первой. Три друга откроют достижение «Лидер вайба»"
    )
    if city:
        text += f"\n\n{city_progress(city)}\nШкала твоего города сдвинулась"
    return text


# =========================================================
# «ПОЗВАТЬ ПОДРУГУ» И VIP
# =========================================================

MENU_INVITE = "💌 Позвать подругу"
BTN_SHARE_FRIEND = "Переслать подруге"
BTN_WHO_LIKED = "💎 Кто меня лайкнул"
BTN_INVITE = "💌 Позвать подругу"
BTN_WRITE_MATCH = "✍️ Написать"
BTN_FILL_PROFILE_CAMPAIGN = "✍️ Заполнить анкету"

INVITE_SHARE_TEXT = (
    "Нашёл аналог дайвинчика, только без фриков и оценки по внешности, "
    "фото открывается только после взаимного вайба\n\n"
    "Девушкам там вип бесплатно, глянь👇"
)

INVITE_REWARD = "Ты позвал 3 подруги, держи вип на 7 дней💎"

MATCH_TEXT = (
    "У вас взаимный вайб💜\n\n"
    "Не жди пока напишет другой, напиши сам👇"
)


def vip_status(user) -> str:
    if vip.is_forever(user):
        return f"{VIP_BADGE} <b>VIP навсегда</b>: ты выше в ленте и видишь, кто тебя лайкнул"
    return (
        f"{VIP_BADGE} <b>VIP до {user['vip_until']:%d.%m}</b>: "
        "ты выше в ленте и видишь, кто тебя лайкнул"
    )


def invite_screen(user, ref_link: str, qualified: int) -> str:
    lines = [
        plain_title("💌", "Позвать подругу"),
        "",
        "Подругам VIP бесплатно, а тебе за каждые 3 подруги — VIP на 7 дней💎",
        "VIP: 💎 в анкете, ты выше в ленте и видишь, кто тебя лайкнул",
        "",
        "Подруга засчитывается, когда заполнит анкету с фото и зайдёт ещё раз на следующий день",
        "",
        f"Засчитано подруг: <b>{qualified % 3}/3</b>"
        + (f" (до следующего VIP) · всего {qualified}" if qualified >= 3 else ""),
    ]
    if user and vip.is_vip(user):
        lines += ["", vip_status(user)]
    lines += ["", "Твоя ссылка👇", ref_link]
    return "\n".join(lines)


def who_liked(people: list, user) -> str:
    if not people:
        return f"{VIP_BADGE} <b>Кто меня лайкнул</b>\n\nПока никто. Полистай анкеты: вайбы приходят в ответ"
    lines = [f"{VIP_BADGE} <b>Кто меня лайкнул</b> · {len(people)}", ""]
    for p in people[:30]:
        line = f"💜 {esc(p['full_name'])}"
        if p["age"]:
            line += f", {p['age']}"
        if p["city"]:
            line += f" · {esc(p['city'])}"
        lines.append(line + _badge(p))
    if len(people) > 30:
        lines.append(f"…и ещё {len(people) - 30}")
    lines += ["", "Фото откроется, когда ответишь вайбом. Жми «Посмотреть» — они первыми в ленте"]
    return "\n".join(lines)


def who_liked_locked(count: int) -> str:
    who = plural(count, "человек", "человека", "человек")
    return (
        f"{VIP_BADGE} <b>Кто меня лайкнул</b>\n\n"
        f"Тебя лайкнули: <b>{count}</b> {who}. Список сразу всех — для VIP\n\n"
        "VIP дают за 3 подруги: позови их по своей ссылке, им VIP бесплатно"
    )


# Шаблоны рассылки из админки: {ref_link} — личная ссылка получателя
CAMPAIGNS = {
    "ref_boys1": {
        "title": "Парням: позови подруг (VIP на 7 дней, 1000₽)",
        "sticker": "sticker_3_vip_7days",
        "button": "invite",
        "text": (
            "Нас уже 500🔥\n\n"
            "Но девушек пока мало, сам понимаешь\n\n"
            "Позови подруг, им вип бесплатно, а тебе за 3 подруги вип на 7 дней\n\n"
            "Ещё среди всех кто приведёт хотя бы одну разыграю 1000₽\n\n"
            "Твоя ссылка👇\n"
            "{ref_link}"
        ),
    },
    "vip_girls1": {
        "title": "Девушкам: дарю VIP",
        "sticker": "sticker_2_vip_girls",
        "button": "invite",
        "text": (
            "Привет, спасибо что ты с нами💜\n\n"
            "Дарю тебе вип, теперь ты выше в ленте и видишь кто тебя лайкнул\n\n"
            "Позовёшь подруг, им тоже вип бесплатно👇\n"
            "{ref_link}"
        ),
    },
    "fill1": {
        "title": "Без анкеты: доделай анкету",
        "sticker": None,
        "button": "fill",
        "text": (
            "Ты так и не доделал анкету😅\n\n"
            "Без неё тебя никто не видит, а тут уже 500 человек. Заполни за минуту и погнали👇"
        ),
    },
}
# какую кампанию девушка получает сразу после анкеты (вместе с VIP)
GIRLS_CAMPAIGN = "vip_girls1"

SEGMENTS = {
    "male": "👨 Парни",
    "female": "👩 Девушки",
    "noprofile": "📝 Без анкеты",
    "all": "👥 Все",
}


# Вайб-час
BTN_VH_GO = "Найти вайб"
BTN_VH_OFF = "Не напоминать"
BTN_VH_ON = "Напоминать снова"
VH_OFF = "Ок, про вайб-час больше не напоминаю"
VH_ON = "Снова буду напоминать про вайб-час в 20:50"


def vibe_hour_soon(online: int) -> str:
    # число «в сети» только настоящее и только когда оно не пугает пустотой
    crowd = (
        f" В Вайбометре уже {online} {plural(online, 'человек', 'человека', 'человек')} в сети"
        if online >= 3 else ""
    )
    return (
        f"{title('bolt', 'Через 10 минут вайб-час')}\n\n"
        "С 21:00 до 22:00 все заходят одновременно, и первыми "
        f"показываются те, кто сейчас в сети.{crowd}"
    )

# «Тайная симпатия»
CRUSH_START = (
    f"{title('eye', 'Тайная симпатия')}\n\n"
    "Отметь @username тех, кто тебе нравится. Никто не узнает, "
    "пока человек не отметит тебя в ответ. Тогда вам обоим придёт уведомление"
)


def crush_mutual(partner) -> str:
    return (
        f"{title('heart', 'Взаимная тайная симпатия')}\n\n"
        f"Ты и {mention(partner)} отметили друг друга. "
        "Кажется, пора написать"
    )


# «Проверь вайб с другом»
VT_START = (
    f"{title('spark', 'Проверь вайб с другом')}\n\n"
    "7 вопросов «что выберешь», потом отправь ссылку другу, "
    "своей половинке или в чат. Как ответят, увидите, на сколько процентов совпал ваш вайб"
)
VT_NO_APP = "Тест открывается в приложении, а оно сейчас недоступно. Попробуй чуть позже"
VT_NOT_FOUND = "Этот тест уже удалён. Сделай свой и отправь друзьям 👇"


def vt_invite(owner_name: str) -> str:
    return (
        f"{title('spark', 'Проверим ваш вайб?')}\n\n"
        f"Тест от <b>{esc(owner_name)}</b>: 7 вопросов «что выберешь». "
        "Ответь на них и узнаешь, на сколько процентов вы совпали. Анкета не нужна"
    )


def vt_friend_done(name: str, percent: int) -> str:
    return (
        f"{e('fire')} Твой тест пройден: <b>{esc(name)}</b>, "
        f"<b>{percent}% вайба</b>\n\nСмотри, в чём вы совпали 👇"
    )
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
        verdict = f"Хороший общий вайб {e('hands')}"
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
        f"Вопросов: {s['questions']} · игр: {s['games']}\n\n"
        "Неделя для роликов: /week · партнёрские ссылки: /sources"
    )


def admin_sources(rows) -> str:
    hint = (
        "Метка в био или посте: t.me/vibemeter_bot?start=<i>метка</i> "
        "(латиница, цифры, _), например start=shahichat. "
        "Для партнёров с тестом сразу: start=vtp_<i>метка</i>"
    )
    if not rows:
        return "Переходов по меткам пока нет\n\n" + hint
    lines = ["📈 <b>Источники</b> (пришли · новых · анкеты · тест)", ""]
    for r in rows:
        lines.append(
            f"<code>{esc(r['tag'])}</code>: {r['came']} · {r['new']} · {r['profiles']} · {r['tested']}"
        )
    lines += ["", hint]
    return "\n".join(lines)


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
                f"{e('lock')} {ach_name} · {hint}\n"
                f"      {_bar(s[key], goal)} {min(s[key], goal)}/{goal}"
            )
    return "\n".join(lines)


# =========================================================
# МОДЕРАЦИЯ ФОТО
# =========================================================

PHOTO_WARNING = (
    "📸 <b>Фото убрали</b>\n\n"
    "В Вайбометре только своё фото с лицом: так честно для всех. "
    "Анкета скрыта из поиска, пока нет фото. Пришли сюда своё фото, где видно лицо, "
    "и она сразу вернётся"
)
PROFILE_HIDDEN = (
    "📝 <b>Анкету скрыли</b>\n\n"
    "В ней мат, пошлость или оскорбления. Заполни её заново по-человечески: /start"
)
PROFILE_BAD_INPUT = "🚫 Так в анкете нельзя — напиши по-другому"
PROFILE_REDO = f"{title('star', 'Анкету нужно заполнить заново')}\n\nНажми /start — это пара минут"

# предупреждения: общий счёт за фото, мат и анкету — два, на третье бан
REASON_PHOTO = "фото без лица или чужое"
REASON_WORDS = "мат, пошлость или оскорбления в сообщении"
REASON_PROFILE = "мат, пошлость или оскорбления в анкете"
BANNED_PREFIX = "🚫 Аккаунт заблокирован"


def strike_warning(reason: str, n: int, limit: int) -> str:
    if n < limit:
        return (
            f"⚠️ <b>Предупреждение {n} из {limit}</b>: {reason}\n"
            "После второго предупреждения следующее нарушение — блокировка"
        )
    return (
        f"⚠️ <b>Последнее предупреждение</b> ({n} из {limit}): {reason}\n"
        "Следующее нарушение — блокировка аккаунта"
    )


def strike_banned(reason: str) -> str:
    return f"{BANNED_PREFIX}: {reason}. Это третье нарушение правил Вайбометра"
PHOTO_NEEDED = (
    f"{title('star', 'Не хватает фото')}\n\n"
    "Пришли сюда своё фото, где видно лицо, и анкета появится в поиске\n\n"
    + PHOTO_RULE
)
PHOTO_USE_SETTINGS = "Поменять фото можно в Mini App (профиль) или через «Настройки» → «Изменить анкету»"
PHOTO_BACK = f"{title('heart', 'Фото на месте')}\n\nАнкета снова в поиске"


# =========================================================
# РАССЫЛКА: личная строка + голосование за следующую функцию
# =========================================================

# ключ → (кнопка, строка в сообщении)
FEATURES = {
    "crush": ("💘 Проверь краша", "💘 <b>Проверь краша</b> — анонимный тест для того, кто нравится. Имя откроется, только если вы оба согласны"),
    "myvibe": ("🪞 Твой вайб", "🪞 <b>Твой вайб</b> — тест о себе и карточка для сторис"),
    "real": ("🛡 Галочка «Настоящий»", "🛡 <b>Галочка «Настоящий»</b> — селфи с жестом, чтобы не было фейков"),
    "firstmsg": ("♟ Оцени первое сообщение", "♟ <b>Оцени первое сообщение</b> — после мэтча: ?? зевок, ! хорошо, !! бриллиант"),
}
VOTE_THANKS = "Голос принят: {name}. Можно передумать до итогов"
NEWS_OFF = "Ок, новости больше не присылаю. Вернуть: /news"
NEWS_ON = "Ок, новости снова будут приходить (не чаще раза в неделю)"
BTN_NEWS_OFF = "Не присылать новости"
CHANNEL_URL = "https://t.me/vibemeter_news"
BTN_CHANNEL = "Канал Вайбометра"
BTN_FILL_PROFILE = "Заполнить анкету"
BTN_VT = "Проверь вайб с другом"
BTN_SEE_VIBES = "Посмотреть вайбы"
BTN_FIND = "Найти вайб"


def broadcast_text(person: dict, total: int) -> str:
    """Личная строка по состоянию человека + голосование."""
    if person["age"] is None:
        personal = (
            "У тебя ещё нет анкеты, поэтому тебя никто не видит. "
            "Это две минуты, фото откроется только при взаимном вайбе\n"
            "А без анкеты можно прямо сейчас проверить вайб с другом"
        )
    elif not person["photo_id"]:
        personal = "Анкета почти готова: не хватает фото. Пришли сюда своё фото с лицом, и ты в поиске"
    elif person["incoming"]:
        n = person["incoming"]
        personal = (
            f"{e('eye')} Тебя ждут <b>{n}</b> {plural(n, 'вайб', 'вайба', 'вайбов')} без ответа. "
            "Загляни, вдруг взаимно"
        )
    else:
        personal = (
            f"{e('bolt')} Каждый вечер с 21 до 22 — вайб-час: больше всего людей в сети, "
            "и они в поиске первыми"
        )
    lines = [
        title("heart", f"Нас уже {total}, спасибо, что ты тут"),
        "",
        personal,
        "",
        f"{e('crown')} <b>Что сделать следующим?</b> Выбери одно — сделаем то, что наберёт больше голосов:",
        "",
    ]
    lines += [line for _, line in FEATURES.values()]
    if person["age"] is not None:
        lines += ["", f"🤳 {PHOTO_RULE}"]
    lines += ["", "📣 Итоги голосования, что выбирают люди и новые функции — в нашем канале"]
    return "\n".join(lines)


# =========================================================
# ОПИСАНИЕ БОТА (ставится при старте, BotFather трогать не нужно)
# =========================================================

# «О боте» в профиле и в ссылках, до 120 символов
BOT_SHORT_DESCRIPTION = "Знакомства по вайбу, а не по фото. Фото откроется, только когда вайб взаимный. 18+ · @vibemeter_news"

# экран пустого чата до «Старт», до 512 символов
BOT_DESCRIPTION = (
    "Вайбометр — знакомства, где сначала совпадает вайб, а потом внешность\n\n"
    "💜 Отправляй вайбы по интересам и характеру\n"
    "🔒 Фото откроется, только когда вайб взаимный\n"
    "🎮 Игры на двоих, анонимные вопросы, вайб дня\n"
    "⚡ Вайб-час каждый вечер 21–22 МСК\n\n"
    "Без анкеты можно проверить вайб с другом. Только 18+\n"
    "Новости и голосования: @vibemeter_news\n\n"
    "Жми «Старт» 👇"
)


# =========================================================
# «МЫ СНОВА В СТРОЮ» (после сбоя 27.10)
# =========================================================

SORRY_TEXT = (
    f"{title('heart', 'Мы снова в строю')}\n\n"
    f"Ночью Вайбометр ненадолго прилёг: мы обновлялись, чтобы бот выдерживал больше людей {e('bolt')}\n"
    "Прости, что пришлось подождать\n\n"
    f"{e('hands')} Всё работает: вайбы, вопросы и игры на месте. Можно продолжать общаться\n\n"
    f"{e('star')} Новости и голосования — в нашем канале"
)
