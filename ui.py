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
from puzzles import stars


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


# Пак владельца «Шах и Чат» (t.me/addemoji/shahichat, 17.11): порядок как в
# assets/emoji/pack_100 (01_m_brilliant … 33_flag). При старте bot.load_emoji_pack
# берёт id из Telegram и кладёт сюда; до загрузки — запасные из старого набора.
EMOJI_PACK = "shahichat"
PACK_ORDER = [
    ("m_brilliant", "💎"), ("m_good", "✅"), ("m_dubious", "🤔"), ("m_blunder", "❌"), ("m_mate", "🟣"),
    ("pawn", "♟"), ("knight", "🐴"), ("bishop", "♝"), ("rook", "🏰"), ("queen", "👸"), ("king", "🤴"),
    ("daily", "📅"), ("fire_g", "🔥"), ("trophy_w", "🏆"), ("star_w", "⭐"), ("rating", "📊"), ("target", "🎯"),
    ("bolt_g", "⚡"), ("shield", "🛡"), ("gift", "🎁"), ("chat_w", "💬"), ("bell", "🔔"), ("settings", "⚙️"),
    ("more", "💬"), ("cross", "✖️"), ("check", "✔️"), ("crown_gold", "👑"), ("knight_gold", "🏅"),
    ("fire_x5", "🔥"), ("timer", "⏱"), ("podium", "🥇"), ("board", "🏁"), ("flag", "🏁"),
]
for _name, _fb in PACK_ORDER:
    NEON.setdefault(_name, (NEON["crown"][0], _fb))
# какие иконки пака уже получили id из Telegram (до загрузки значки ходов — текстом)
PACK_LOADED: set[str] = set()
# старые имена, которые теперь рисуем иконками пака (зелёный стиль)
PACK_ALIASES = {
    "fire": "fire_g", "bolt": "bolt_g", "crown": "crown_gold", "star": "star_w", "trophy": "trophy_w",
    "chat": "chat_w", "gear": "settings", "diamond": "m_brilliant", "hands": "gift", "spark": "knight",
    "speedo": "timer", "lock": "shield", "eye": "target", "gamepad": "board", "candy": "daily", "heart": "check",
}


MENU_PACK_ICONS = {
    "Играть": "knight", "Открыть игру": "board", "Задача дня": "daily", "Разбор переписки": "chat_w",
    "База ходов": "target", "Вопрос автору": "bell", "Мой рейтинг": "rating", "Топ игроков": "trophy_w",
}


# имена файлов assets/emoji/pack_100 -> имена в PACK_ORDER (кэш сопоставления хранит имена файлов)
FILE_NAMES = {"fire": "fire_g", "trophy": "trophy_w", "star": "star_w", "bolt": "bolt_g", "chat": "chat_w",
              "crown": "crown_gold"}


def load_pack(stickers) -> int:
    """id эмодзи пака по порядку загрузки -> NEON. Возвращает, сколько подставлено."""
    n = 0
    for (name, fallback), st in zip(PACK_ORDER, stickers):
        if st.custom_emoji_id:
            NEON[name] = (st.custom_emoji_id, fallback)
            PACK_LOADED.add(name)
            n += 1
    if n:
        apply_pack()
    return n


def apply_pack():
    """Меню -> иконки пака, тексты-константы пересобрать с иконками."""
    MENU_ICONS.update(MENU_PACK_ICONS)
    refresh_texts()


def load_pack_map(mapping: dict) -> int:
    """Пак по совпадению картинок: {имя файла или имя пака: custom_emoji_id}."""
    fb = dict(PACK_ORDER)
    n = 0
    for name, eid in mapping.items():
        name = FILE_NAMES.get(name, name)
        if name in fb:
            NEON[name] = (eid, fb[name])
            PACK_LOADED.add(name)
            n += 1
    if n:
        apply_pack()
    return n


def _pack_name(name: str) -> str | None:
    """Имя -> иконка нашего пака, если она загружена. Старый неоновый набор не используем (18.11)."""
    n = PACK_ALIASES.get(name, name)
    return n if n in PACK_LOADED else None


def e(name: str) -> str:
    """Эмодзи в тексте (HTML): иконка пака «Шах и Чат», иначе обычный эмодзи."""
    n = _pack_name(name)
    fallback = NEON[name][1] if name in NEON else ""
    if not n:
        return fallback
    return f'<tg-emoji emoji-id="{NEON[n][0]}">{fallback or NEON[n][1]}</tg-emoji>'


# значки ходов -> иконки пака (01–05: !! ! ?! ?? #); «!?» и «?» рисуем ближайшими
MARK_ICONS = {"!!": "m_brilliant", "!": "m_good", "!?": "m_good", "?!": "m_dubious",
              "?": "m_dubious", "??": "m_blunder", "#": "m_mate"}
MARK_FALLBACK = {"!!": "‼️", "!": "❗", "!?": "⁉️", "?!": "⁉️", "?": "❓", "??": "❓", "#": "#️⃣"}


def mark(m: str) -> str:
    """Значок хода в тексте: иконка из пака «Шах и Чат», пока пака нет — сам знак."""
    name = MARK_ICONS.get(m)
    if name in PACK_LOADED:
        return f'<tg-emoji emoji-id="{NEON[name][0]}">{MARK_FALLBACK[m]}</tg-emoji>'
    return f"<b>{escape(m)}</b>"


def marks_legend() -> str:
    return f"{mark('??')} зевок · {mark('?!')} сомнительно · {mark('!')} хороший · {mark('!!')} бриллиант · {mark('#')} мат"


# фигуры званий -> иконки пака
RANK_ICONS = {"Пешка": "pawn", "Конь": "knight", "Слон": "bishop", "Ладья": "rook", "Ферзь": "queen",
              "Гроссмейстер": "king"}


def rank_icon(rank: str) -> str:
    name = RANK_ICONS.get(rank)
    if name in PACK_LOADED:
        return e(name)
    return RANK_EMOJI.get(rank, "♟")


def icon(name: str) -> str | None:
    """id иконки кнопки из пака; None — кнопка без иконки (старый набор не показываем)."""
    n = _pack_name(name)
    return NEON[n][0] if n else None


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
MENU_INVITE = "Позвать подругу"
MENU_CHESS = "Шах и чат"
MENU_PLAY = "Играть"
MENU_APP = "Открыть игру"
MENU_DAILY = "Задача дня"
MENU_RAZBOR = "Разбор переписки"
MENU_BAZA = "База ходов"
MENU_ASK = "Вопрос автору"
MENU_TOP = "Топ игроков"
MENU_FACT = "Факт дня"
MENU_ME = "Мой рейтинг"
MENU_FRIEND = "Позвать друга"

MENU_ICONS = {
    MENU_FIND: "bolt",
    MENU_LIKES: "heart",
    MENU_PROFILE: "star",
    MENU_GAMES: "gamepad",
    MENU_STATS: "crown",
    MENU_SETTINGS: "gear",
    MENU_INVITE: "diamond",
    MENU_CHESS: "crown",
    MENU_PLAY: "crown",
    MENU_DAILY: "fire",
    MENU_RAZBOR: "chat",
    MENU_BAZA: "spark",
    MENU_ASK: "eye",
    MENU_TOP: "trophy",
    MENU_FACT: "spark",
    MENU_ME: "star",
    MENU_FRIEND: "hands",
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
    MENU_INVITE: {"💌 Позвать подругу"},
    MENU_CHESS: {"♟ Шах и чат"},
    MENU_PLAY: {"Шах и чат", "♟ Шах и чат"},
    MENU_DAILY: set(),
    MENU_RAZBOR: set(),
    MENU_BAZA: set(),
    MENU_ASK: set(),
    MENU_TOP: set(),
    MENU_FACT: set(),
    MENU_ME: set(),
    MENU_FRIEND: set(),
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
BTN_OPEN_APP = "Открыть «Шах и Чат»"
BTN_ACHIEVEMENTS = "Зал славы"
BTN_EDIT = "Изменить анкету"
BTN_SEARCH = "Кого искать"
BTN_BLOCKED = "Заблокированные"
BTN_DELETE = "Удалить профиль"
BTN_DELETE_YES = "Да, удалить"
BTN_BACK = "Назад"
BTN_ACCEPT = "Мне есть 14, поехали"
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

def consent() -> str:
    return (
        "Привет. Тут тренируют переписку ♟\n\n"
        f"Она пишет — ты ходишь, я ставлю оценку как в шахматах: {mark('!!')} или {mark('??')} зевок\n\n"
        "🤖 Это тренажёр, а не живая девушка\n"
        "🔞 С 14 лет\n\n"
        "Согласен с /privacy? Поехали"
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
    "<b>Возраст:</b> с 14 лет\n\n"
    "Вопросы по данным можно задать администратору бота"
)


# =========================================================
# START И МЕНЮ
# =========================================================

def welcome_back(streak: int) -> str:
    text = "С возвращением\n\nЗадача дня уже ждёт –> /daily\nСыграть партию –> /play"
    if streak >= 2:
        text += f"\n{e('fire')} Серия {days(streak)}"
    return text


MAIN_MENU = plain_title("🏠", "Главное меню")
NEED_START = "Напиши /start, и начнём"
UNKNOWN = "Не понял 🙂 Выбери что-нибудь в меню"
CANCELLED = "Окей, отменили"
PHOTO_UPDATED = "📸 Новое фото анкеты из Вайбометра"
BANNED = "🚫 Аккаунт заблокирован за нарушение правил «Шах и Чат»"


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
    "Извини, «Шах и Чат» только для тех, кому есть 18. "
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


def _badge(person) -> str:
    return f" {e('diamond')}" if vip.is_vip(person) else ""


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

BTN_SHARE_FRIEND = "Переслать подруге"
BTN_WHO_LIKED = "Кто меня лайкнул"
BTN_INVITE = "Позвать подругу"

INVITE_SHARE_TEXT = (
    "Нашёл аналог дайвинчика, только без фриков и оценки по внешности, "
    "фото открывается только после взаимного вайба\n\n"
    "Девушкам там вип бесплатно, глянь👇"
)

INVITE_REWARD = f"Ты позвал 3 подруги, держи вип на 7 дней{e('diamond')}"

MATCH_TEXT = (
    f"У вас взаимный вайб{e('heart')}\n\n"
    "Не жди пока напишет другой, напиши сам👇"
)


def vip_status(user) -> str:
    if vip.is_forever(user):
        return f"{e('diamond')} <b>VIP навсегда</b>: ты выше в ленте и видишь, кто тебя лайкнул"
    return (
        f"{e('diamond')} <b>VIP до {user['vip_until']:%d.%m}</b>: "
        "ты выше в ленте и видишь, кто тебя лайкнул"
    )


def invite_screen(user, ref_link: str, qualified: int) -> str:
    lines = [
        title("heart", "Позвать подругу"),
        "",
        f"Подругам VIP бесплатно, а тебе за каждые 3 подруги — VIP на 7 дней{e('diamond')}",
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
        return f"{e('diamond')} <b>Кто меня лайкнул</b>\n\nПока никто. Полистай анкеты: вайбы приходят в ответ"
    lines = [f"{e('diamond')} <b>Кто меня лайкнул</b> · {len(people)}", ""]
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
        f"{e('diamond')} <b>Кто меня лайкнул</b>\n\n"
        f"Тебя лайкнули: <b>{count}</b> {who}. Список сразу всех — для VIP\n\n"
        "VIP дают за 3 подруги: позови их по своей ссылке, им VIP бесплатно"
    )


# Шаблоны рассылки из админки: {ref_link} — личная ссылка получателя
CAMPAIGNS = {
    "pivot1": {
        "title": "♟ Вайбометр теперь игра «Шах и чат»",
        "audience": "all",
        "sticker": None,
        "button": "play",
        "text": (
            f"{title('crown', 'Вайбометр стал игрой')}\n\n"
            "Знакомств больше нет — теперь тут «Шах и чат». Ситуация из переписки, твой ход, "
            "а я оцениваю его как в шахматах: !! бриллиант или ?? зевок\n\n"
            "Объяснения — из настоящих исследований: как люди общаются и почему расстаются. "
            "Есть рейтинг, топ игроков и задача дня\n\n"
            "Проверь, какой у тебя уровень переписки👇"
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
        "Метка в био или посте: t.me/&lt;бот&gt;?start=<i>метка</i> "
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
    return f"{BANNED_PREFIX}: {reason}. Это третье нарушение правил «Шах и Чат»"
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
BOT_NAME = "Шах и Чат"
BOT_SHORT_DESCRIPTION = "Тренажёр переписки «Шах и чат»: ИИ играет за неё, каждый твой ход — оценка как в шахматах"

# экран пустого чата до «Старт», до 512 символов
BOT_DESCRIPTION = (
    "Шах и чат — тренажёр переписки\n\n"
    "♟ ИИ играет за неё, ты отвечаешь как умеешь\n"
    "?? зевок · ? слабый · ! хороший · !! блестящий · # мат\n"
    "🔥 Задача дня, рейтинг от Пешки до Гроссмейстера\n"
    "📋 Разбор твоей переписки и база готовых ходов\n\n"
    "Это ИИ, а не живая девушка. С 14 лет\n"
    "Канал: t.me/shahichat\n\n"
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


# =========================================================
# «ШАХ И ЧАТ» — задачи по переписке
# =========================================================

BTN_PZ_NEXT = "Следующая задача"
BTN_FACT = "Факт об общении"


def puzzle_text(puzzle, number: int, rating: int, rank: str) -> str:
    return (
        f"{title('daily', f'Задача {number}')}\n\n"
        f"<blockquote>{esc(unquote(puzzle['chat']))}</blockquote>\n\n"
        f"Твой ход 👇 · {rating} · {rank}"
    )


def unquote(text: str) -> str:
    """Без «ёлочек» и скобок-кавычек: «Она: «Ок»» -> «Она: Ок»."""
    return text.replace("«", "").replace("»", "").replace('"', "")


def puzzle_result(move: str, my_mark: str, name: str, why: str, best: str, delta: int, rating: int, rank: str,
                  others: list | None = None) -> str:
    sign = f"+{delta}" if delta > 0 else ("±0" if delta == 0 else str(delta))
    lines = [f"{mark(my_mark)} <b>{name}</b> · {sign} · {rating}", esc(unquote(why))]
    if others:
        lines.append("")
        for text, m, w in others:
            lines.append(f"{mark(m)} {esc(unquote(text))} — <i>{esc(unquote(w))}</i>")
    return "\n".join(lines)


PUZZLES_DONE = (
    f"{title('trophy', 'Все задачи решены')}\n\n"
    "Новые задачи появляются регулярно. А пока — факт об общении 👇"
)

BTN_PZ_TOP = "Топ игроков"
BTN_PZ_SHARE = "Скинуть задачу другу"
PZ_SHARE_TEXT = "Как бы ты ответил? Проверь себя в «Шах и чат» — оценю твой ход как в шахматах ♟"
PZ_FRIEND = "Тебе скинули задачу из «Шах и чат». Твой ход 👇"


def chess_top(rows, place: int, total: int, me_rating: int) -> str:
    lines = [title("trophy", "Топ «Шах и чат»"), ""]
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(rows):
        mark = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{mark} {esc(r['full_name'] or 'Игрок')} — <b>{r['chess_rating']}</b> · задач {r['solved']}")
    if not rows:
        lines.append("Пока никто не играл — будь первым")
    lines.append("")
    if place:
        lines.append(f"{e('fire')} Ты на <b>{place}</b> месте из {total} · рейтинг {me_rating}")
    else:
        lines.append("Реши первую задачу — и ты в рейтинге")
    return "\n".join(lines)

BTN_PZ_SOLVE = "Решить задачу"
BTN_PZ_OFF = "Не напоминать"
PZ_OFF = "Ок, про задачу дня больше не напоминаю. Вернуть: /chess_on"
PZ_ON = "Снова буду напоминать о задаче дня в 13:00"


def chess_reminder(rating: int, rank: str) -> str:
    return (
        f"{title('daily', 'Задача дня ждёт')}\n\n"
        "Новая переписка — твой ход. Минута, и рейтинг подрастёт\n\n"
        f"{e('fire')} Сейчас: <b>{rating}</b> · {rank}"
    )


def streak_reminder(streak: int, rating: int) -> str:
    return (
        f"{title('fire', f'Серия {days(streak)} сгорит в полночь')}\n\n"
        "Одна задача — минута, и серия живёт дальше\n\n"
        f"Рейтинг: <b>{rating}</b>"
    )


# ---------- закрытый бета-тест (17.11) ----------
BTN_BETA_OPEN = "Открыть игру"
BTN_APP_GAME = "Открыть игру"
BTN_FEEDBACK = "Оставить отзыв"


def beta_feedback_reminder() -> str:
    return (
        f"{e('bell')} <b>Ты в бета-тесте «Шах и Чат»</b>\n\n"
        "Сыграй пару партий в игре и напиши пару слов: что зашло, что сломалось, чего не хватает\n\n"
        "Читаю каждый отзыв сам — по ним и доделываем игру 🙏"
    )
BETA_OPEN = e("knight") + " Тест закончился — игра открыта для всех. Жми 👇"


def beta_in(num: int, slots: int) -> str:
    return (
        f"{title('knight', f'Ты в бета-тесте: место {num} из {slots}')}\n\n"
        "Это тестовая версия «Шах и Чат»: партии по переписке как в шахматах, рейтинг Эло, задачи. "
        "Где-то может быть сыро — так и задумано, чиним по вашим отзывам\n\n"
        "Одно условие: после пары партий напиши своё мнение прямо в игре. Это и есть твоя роль тестера 🙏"
    )


def beta_full(pos: int, slots: int) -> str:
    return (
        f"{title('timer', 'Все места в тесте заняты')}\n\n"
        f"{slots} самых быстрых уже играют. Ты в очереди: {pos}-й. "
        "Напишем, как только откроем игру для всех — уже скоро"
    )


def beta_admin(st: dict, slots: int) -> str:
    lines = [
        "🧪 <b>Бета-тест</b>",
        "",
        f"Тестеров: <b>{st['testers']}</b> из {slots}",
        f"В очереди: {st['waiting']}",
        f"Отзывов: {st['reviewed']} · средняя оценка: {st['stars'] or '—'}",
        f"Партий доиграно: {st['games']}",
        "",
        "Ссылка для теста: t.me/&lt;бот&gt;?start=beta",
        "Релиз: BETA_SLOTS=0 в переменных Bothost",
    ]
    if st["last"]:
        lines += ["", "<b>Последние отзывы</b>"]
        for f in st["last"]:
            who = f"@{f['username']}" if f.get("username") else esc(f.get("full_name") or str(f["user_id"]))
            lines.append(f"{'⭐' * (f['stars'] or 0)} {who}: {esc(f['text'][:300])}")
    return "\n".join(lines)


# =========================================================
# ПОСЛЕ ПОВОРОТА: знакомства закрыты, теперь игра
# =========================================================

DATING_CLOSED = (
    f"{title('crown', 'Знакомств больше нет — теперь мы игра')}\n\n"
    "Вайбометр стал «Шах и чат»: ситуация из переписки, твой ход — оценка как в шахматах. "
    "Жми «Шах и чат» внизу 👇"
)
WELCOME_NEW = (
    f"{title('crown', 'Поехали')}\n\n"
    "Вот первая задача. Выбирай ход — я оценю. Меню внизу: топ игроков, факт дня и твой рейтинг"
)
BTN_SHARE_FRIEND_GAME = "Переслать другу"
FRIEND_SHARE_TEXT = "Проверь, как ты переписываешься: бот оценивает ходы в чате как в шахматах ♟ !! или ?? — посмотрим"


def friend_invite(link: str) -> str:
    return (
        f"{title('hands', 'Позвать друга')}\n\n"
        "Скинь другу задачу дня — посмотрим, кто сыграет лучше\n\n"
        f"Ссылка: {link}"
    )


def my_rating(rating: int, rank: str, solved: int, total: int, brilliant: int, place: int, players: int) -> str:
    lines = [
        title("star", "Мой рейтинг"),
        "",
        f"{e('fire')} Рейтинг: <b>{rating}</b> · {rank}",
        f"{e('board')} Решено задач: <b>{solved}</b> из {total}",
        f"{mark('!!')} Бриллиантов: <b>{brilliant}</b>",
    ]
    lines.append(f"{e('trophy_w')} Место: <b>{place}</b> из {players}" if place else f"{e('trophy_w')} Реши первую задачу — и ты в топе")
    return "\n".join(lines)


def fact_of_day(rendered: str) -> str:
    return fact_head(rendered).replace("<b>Факт</b>", "<b>Факт дня</b>", 1)


def fact_head(rendered: str) -> str:
    """🧠 в заголовке факта -> иконка пака."""
    return rendered.replace("🧠", e("bolt_g") if "bolt_g" in PACK_LOADED else "🧠", 1)


# =========================================================
# ТРЕНАЖЁР ПЕРЕПИСКИ (ТЗ 16.11) — стиль: на «ты», коротко, стрелки «–>»
# =========================================================

SHAH_CHANNEL_URL = "https://t.me/shahichat"
BTN_SHAH_CHANNEL = "Канал"
BTN_PLAY_AGAIN = "Ещё партию"
BTN_DAILY = "Задача дня"
BTN_RANDOM = "Случайная"
BTN_ASK_FORWARD = "Передать автору"
BTN_PLAY = "Играть"

TRAINER_WELCOME = (
    f"Готово {e('knight')}\n\n"
    "Жми «Открыть игру» — там партии как в шахматах и рейтинг Эло. "
    "Или «Играть» — задачи прямо тут"
)

PLAY_CHOOSE = "Выбирай партию. Звёзды — сложность: чем больше, тем больше очков за победу"
PLAY_LIMIT = "На сегодня бесплатные партии всё (5 в день). Завтра продолжим\n\nА пока –> /daily или /baza"
LLM_SOON = "Партии с ИИ включатся совсем скоро. Пока держи быструю задачу 👇"
LLM_BUSY = "Модель не ответила. Попробуй ещё раз через минуту"
YOUR_MOVE = "Твой ход –> пиши ответ сюда"
YOU_FIRST = "Ты пишешь первым –> пиши сюда"
GAME_NONE = "Партии сейчас нет. Начать –> /play"
TEXT_ONLY = "Отвечай текстом, как в переписке"
TOO_LONG = "Слишком длинно для переписки. Сократи до пары строк"

STAMPS = {
    "mate": "♚ МАТ: тебя проверили",
    "stalemate": "⏸ ПАТ: разговор умер",
    "win": "🏆 ПОБЕДА",
}

def _stamp(result: str) -> str:
    """Итог партии: иконка пака (если загружен) вместо обычного эмодзи в начале."""
    text = STAMPS.get(result, STAMPS["stalemate"])
    name = {"mate": "m_mate", "win": "trophy_w"}.get(result)
    if name and name in PACK_LOADED:
        return f"{e(name)} <b>{text.split(' ', 1)[1]}</b>"
    return f"<b>{text}</b>"


RANK_EMOJI = {"Пешка": "♟", "Конь": "♞", "Слон": "♝", "Ладья": "♜", "Ферзь": "♛", "Гроссмейстер": "♚"}


def game_intro(sit: dict) -> str:
    lines = [f"{e('knight')} <b>{esc(sit.get('title') or sit['key'])}</b> · {'★' * stars(sit['difficulty'])}", "",
             f"<i>{esc(sit['context'])}</i>", ""]
    if sit.get("opening"):
        lines += [f"она: {esc(sit['opening'])}", "", YOUR_MOVE]
    else:
        lines.append(YOU_FIRST)
    return "\n".join(lines)


def move_verdict(v: dict) -> str:
    return f"{mark(v['badge'])} <b>{v['eval']:+.1f}</b>  {esc(unquote(v['coach']))}"


def her_line(text: str) -> str:
    return f"она: {esc(text)}"


def game_result(result: str, before: int, after: int, rank: str, best: str | None, avg: float) -> str:
    diff = after - before
    lines = [
        _stamp(result),
        "",
        f"Средняя оценка ходов: {avg:+.1f}",
        f"Рейтинг: {before} –> <b>{after}</b> ({'+' if diff >= 0 else ''}{diff}) · {rank_icon(rank)} {rank}",
    ]
    if best:
        lines += ["", f"Лучший ход: «{esc(best)}»"]
    return "\n".join(lines)


DAILY_ASK = e("daily") + " <b>Задача дня</b>\n\n<i>{context}</i>\n\nона: {opening}\n\nТвой ход –> один ответ, пиши сюда"


def daily_result(v: dict, better: int, total: int, already: bool = False) -> str:
    head = "Ты уже сыграл задачу дня" if already else "Задача дня сыграна"
    lines = [f"{e('daily')} <b>{head}</b>", "", move_verdict(v)]
    if total > 1:
        lines += ["", f"Ты ответил лучше {better}% игроков (сегодня ответили {total})"]
    else:
        lines += ["", "Ты первый сегодня — посмотрим, кто ответит лучше"]
    if v.get("best_move") and v["badge"] not in ("!!", "#"):
        lines += ["", f"Лучший ход: «{esc(v['best_move'])}»"]
    lines += ["", "Новая задача — завтра. Сыграть партию –> /play"]
    return "\n".join(lines)


RAZBOR_ASK = (
    f"{e('chat_w')} <b>Разбор переписки</b>\n\n"
    "Пришли скрин или текст переписки и одной строкой — чего хочешь (например: «позвать гулять»)\n\n"
    "Имена заменю на «она»/«он», картинку после разбора не храню"
)
RAZBOR_LIMIT = "Бесплатный разбор — один в день. Завтра пришлёшь ещё"
RAZBOR_WAIT = "Разбираю партию… ⏳"
RAZBOR_SOON = "Разбор с ИИ включится совсем скоро. А пока посмотри /baza — там готовые ходы"

BAZA_CHOOSE = e("target") + " <b>База ходов</b>\n\nВыбирай ситуацию — покажу ходы со значками"


def baza_card(item: dict) -> str:
    lines = [f"{e('target')} <b>{esc(unquote(item['title']))}</b>", "", f"она: {esc(item['her'])}", ""]
    for text, badge, why in item["moves"]:
        lines.append(f"{mark(badge)} {esc(text)}\n    <i>{esc(why)}</i>")
    return "\n".join(lines)


ASK_PROMPT = e("bell") + " <b>Вопрос автору</b>\n\nНапиши вопрос одним сообщением. Отвечу сразу, а если надо — передашь автору"
ASK_SENT = "Передал автору 👌 Ответ придёт сюда, когда он прочитает"
ASK_ALREADY = "Этот вопрос уже у автора"
ASK_FORWARDED_NO_LLM = "Передал вопрос автору 👌 Ответ придёт сюда"

REFUSE_MANIPULATION = "такое не разбираю. могу помочь с тем, что написать ей самому"

CRISIS_TEXT = (
    "Слушай, игру на паузу. Похоже, тебе сейчас реально тяжело\n\n"
    "Ты не один. Напиши или позвони тому, кому доверяешь — другу, родным\n\n"
    "Бесплатно и круглосуточно: телефон доверия <b>8-800-2000-122</b>\n"
    "Если опасность прямо сейчас — <b>112</b>\n\n"
    "Я бот и не заменю живого человека, но рядом есть люди, которые помогут"
)

def help_text() -> str:
    return (
        "<b>Что это</b>\n"
        "Тренажёр переписки «Шах и чат». За неё играет ИИ, а не живая девушка\n\n"
        f"<b>Значки</b>\n{marks_legend()}\n\n"
        "<b>Режимы</b>\n"
        "/play — партия 3–5 ходов\n/daily — задача дня, один ответ\n"
        "/razbor — разбор твоей переписки\n/baza — база готовых ходов\n"
        "/me — рейтинг · /top — лидеры · /ask — вопрос автору\n\n"
        "<b>Бесплатно</b>: 5 партий и 1 разбор в день\n\n"
        "<b>Правила</b>\n"
        f"Не учим давить, манипулировать и следить. Пошлость и грубость — сразу {mark('??')} так не играем\n"
        "Автор — не психолог. Ничего не обещаем: это тренировка, а не гарантия\n\n"
        "Канал –> t.me/shahichat"
    )


def trainer_me(rating: int, rank: str, streak: int, games: int, wins: int, best: str | None,
               place: int, total: int, nxt: tuple | None) -> str:
    lines = [
        f"{rank_icon(rank)} <b>{rank}</b> · рейтинг <b>{rating}</b>",
        "",
        f"{e('fire_g')} Серия: {days(streak)}",
        f"{e('board')} Партий: {games} · побед: {wins}",
    ]
    if best:
        lines.append(f"{e('trophy_w')} Лучшая партия: {esc(best)}")
    if place:
        lines.append(f"{e('rating')} Место: {place} из {total}")
    if nxt:
        lines.append(f"\nДо звания «{nxt[1]}»: {nxt[0] - rating}")
    return "\n".join(lines)


def trainer_top(rows, place: int, total: int, rating: int, owner: dict | None = None) -> str:
    lines = [f"{e('trophy_w')} <b>Топ-20</b>", ""]
    if owner:
        lines += [f"{e('crown_gold')} Автор игры: {esc(owner.get('full_name') or 'Артемий')} · {owner.get('chess_rating') or 0}", ""]
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(rows):
        mark = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{mark} {esc(r['full_name'] or 'Игрок')} — <b>{r['chess_rating']}</b>")
    if not rows:
        lines.append("Пока пусто — будь первым –> /play")
    if place:
        lines += ["", f"Ты: {place} место из {total} · {rating}"]
    return "\n".join(lines)


def refresh_texts():
    """Тексты-константы считаются при импорте, когда пака ещё нет (обычные эмодзи).
    После загрузки пака пересчитываем те, где есть e()/title()/mark(), — уже с иконками."""
    import ast
    import re
    from pathlib import Path
    g = globals()
    src = Path(__file__).read_text(encoding="utf-8")
    for node in ast.parse(src).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        seg = ast.get_source_segment(src, node.value) or ""
        if re.search(r"\b(e|title|mark|marks_legend|rank_icon)\(", seg):
            try:
                g[node.targets[0].id] = eval(compile(ast.Expression(node.value), "ui.py", "eval"), g)
            except Exception:
                pass
