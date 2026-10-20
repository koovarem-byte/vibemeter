import html
import logging
import random

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from database import (
    create_user,
    get_user,
    update_user,
    get_admin_stats,
    get_candidates,
    add_like,
    has_like,
    add_skip,
    add_block,
    get_incoming_likes,
    get_stats,
    get_blocked_users,
    delete_user,
    add_report,
    count_reports,
    set_banned,
    dismiss_reports,
    is_banned,
)

from keyboards import (
    main_menu,
    after_profile,
    profile_actions,
    incoming_actions,
    mutual_actions,
    conversation_topics,
    settings_keyboard,
    stats_keyboard,
    game_actions,
    game_keyboard,
    game_result_actions,
    back_keyboard,
    consent_keyboard,
    report_reasons_keyboard,
    admin_report_keyboard,
    REPORT_REASONS,
)

from states import ProfileState, QuestionState
from utils import (
    normalize_interests,
    get_common_interests,
    format_common_interests,
    valid_name,
    valid_age,
    valid_city,
    valid_description,
    is_adult,
    MIN_AGE,
    MAX_AGE,
)

from questions import send_question, submit_answer

from games import (
    start_game,
    get_current_question,
    save_answer,
    complete_game,
    get_result_text,
)

router = Router()

ADMIN_ID = 1771096901


# =========================================================
# БАН: забаненные не пользуются ботом
# =========================================================

BANNED_TEXT = (
    "🚫 Твой аккаунт заблокирован за нарушение правил Вайбометра."
)


async def ban_middleware(handler, event, data):
    user = data.get("event_from_user")

    if user and user.id != ADMIN_ID and await is_banned(user.id):
        if isinstance(event, CallbackQuery):
            await event.answer(BANNED_TEXT, show_alert=True)
        else:
            await event.answer(BANNED_TEXT)
        return None

    return await handler(event, data)


router.message.outer_middleware(ban_middleware)
router.callback_query.outer_middleware(ban_middleware)


@router.message(Command("admin"))
async def admin_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    stats = await get_admin_stats()

    await message.answer(
        "<b>🔥 ВАЙБОМЕТР — ADMIN</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"✅ Профилей: <b>{stats['profiles']}</b>\n"
        f"📸 С фото: <b>{stats['photos']}</b>\n\n"
        f"💜 Лайков: <b>{stats['likes']}</b>\n"
        f"🤝 Взаимных: <b>{stats['mutual']}</b>\n"
        f"👎 Скипов: <b>{stats['skips']}</b>\n\n"
        f"💬 Вопросов: <b>{stats['questions']}</b>\n"
        f"🎮 Игр: <b>{stats['games']}</b>\n"
        f"📅 Сегодня: <b>+{stats['today']}</b>"
    )

# Временные данные активных просмотров
current_profile = {}

# Очередь для вайб-игры
waiting_players = []


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def esc(value):
    """Безопасный вывод пользовательского текста в HTML."""
    if value is None:
        return ""
    return html.escape(str(value))


def calculate_vibe(first, second):
    """
    Примерный процент вайба.
    Это не научный тест — просто оценка по общим интересам и городу.
    """

    first_interests = normalize_interests(first["interests"] or "")
    second_interests = normalize_interests(second["interests"] or "")

    common = get_common_interests(
        first_interests,
        second_interests,
    )

    score = 40

    score += min(len(common) * 10, 40)

    if (
        first["city"]
        and second["city"]
        and first["city"].strip().lower()
        == second["city"].strip().lower()
    ):
        score += 15

    if score > 95:
        score = 95

    return score, common


def profile_text(person, vibe=None, common=None):
    """Красиво формирует карточку пользователя."""

    text = "<b>👤 Профиль</b>\n\n"

    text += f"<b>{esc(person['full_name'])}</b>"

    if person["age"]:
        text += f", {person['age']}"

    if person["city"]:
        text += f"\n📍 {esc(person['city'])}"

    if vibe is not None:
        text += f"\n\n🔥 <b>{vibe}% ВАЙБА</b>"

    if common:
        text += "\n\n💜 <b>Общие интересы:</b>\n"
        text += esc(format_common_interests(common))

    if person["interests"]:
        text += "\n\n🎯 <b>Интересы:</b>\n"
        text += esc(person["interests"])

    if person["description"]:
        text += "\n\n💬 <b>О себе:</b>\n"
        text += esc(person["description"])

    return text


async def send_profile(message, person, viewer_id):
    viewer = await get_user(viewer_id)

    vibe, common = calculate_vibe(viewer, person)

    current_profile[viewer_id] = person["telegram_id"]

    text = profile_text(
        person,
        vibe=vibe,
        common=common,
    )

    keyboard = profile_actions(
        person["telegram_id"]
    )

    # Фото скрыто до взаимного лайка
    await message.answer(
        text
        + "\n\n🔒 <b>Фото откроется после взаимного вайба.</b>",
        reply_markup=keyboard,
    )

async def show_next_profile(message, user_id):
    """Показывает следующую подходящую анкету."""

    viewer = await get_user(user_id)

    if not viewer:
        await message.answer("Сначала напиши /start.")
        return

    candidates = await get_candidates(user_id)

    if not candidates:
        current_profile.pop(user_id, None)
        await message.answer(
            "<b>🔎 Пока больше никого нет</b>\n\n"
            "Ты посмотрел все доступные анкеты. "
            "Загляни позже!",
            reply_markup=main_menu(),
        )
        return

    # Дополнительная проверка пола
    viewer_gender = viewer.get("search_gender") or "all"

    filtered = []

    for person in candidates:
        person_id = person.get("telegram_id")

        if person_id == user_id or not is_adult(person.get("age")):
            continue

        # Фильтр по полу, если поле есть в данных анкеты
        person_gender = person.get("gender")

        if (
            viewer_gender != "all"
            and person_gender
            and person_gender != viewer_gender
        ):
            continue

        filtered.append(person)

    if not filtered:
        current_profile.pop(user_id, None)
        await message.answer(
            "<b>🔎 Подходящих анкет пока нет</b>\n\n"
            "Попробуй зайти позже.",
            reply_markup=main_menu(),
        )
        return

    # Не показываем текущую анкету повторно подряд
    previous_id = current_profile.get(user_id)
    available = [
        person for person in filtered
        if person.get("telegram_id") != previous_id
    ]

    person = random.choice(available or filtered)

    await send_profile(message, person, user_id)

async def finish_profile(state: FSMContext, user_id: int):
    """Получает готовый профиль и показывает его."""

    user = await get_user(user_id)

    await state.clear()

    await user_profile_message(
        None,
        user,
        user_id,
    )


async def user_profile_message(message, user, user_id):
    """Показывает собственный профиль."""

    if not user:
        return

    text = "<b>👤 МОЙ ПРОФИЛЬ</b>\n\n"

    text += f"<b>{esc(user['full_name'])}</b>"

    if user["age"]:
        text += f", {user['age']}"

    if user["city"]:
        text += f"\n📍 {esc(user['city'])}"

    if user["interests"]:
        text += f"\n\n🎯 <b>Интересы:</b>\n{esc(user['interests'])}"

    if user["description"]:
        text += f"\n\n💬 <b>О себе:</b>\n{esc(user['description'])}"

    if user["photo_id"]:
        await message.answer_photo(
            photo=user["photo_id"],
            caption=text,
            reply_markup=after_profile(),
        )
    else:
        await message.answer(
            text,
            reply_markup=after_profile(),
        )


async def notify_mutual(bot, user_id, person_id, title):
    """Взаимный вайб: каждому открываем фото и анкету второго."""

    user = await get_user(user_id)
    person = await get_user(person_id)

    for viewer_id, other in ((user_id, person), (person_id, user)):
        if not other:
            continue

        caption = (
            f"<b>💜 {title}</b>\n\n"
            "🔓 Фото открыто — вы оба выбрали друг друга.\n\n"
            f"<b>{esc(other['full_name'])}</b>"
        )

        if other["age"]:
            caption += f", {other['age']}"

        if other["city"]:
            caption += f"\n📍 {esc(other['city'])}"

        keyboard = mutual_actions(other["telegram_id"])

        try:
            if other["photo_id"]:
                await bot.send_photo(
                    viewer_id,
                    photo=other["photo_id"],
                    caption=caption,
                    reply_markup=keyboard,
                )
            else:
                await bot.send_message(
                    viewer_id,
                    caption,
                    reply_markup=keyboard,
                )
        except Exception:
            logging.exception(
                "Не удалось отправить взаимный вайб %s", viewer_id
            )


# =========================================================
# СОГЛАСИЕ И ПОЛИТИКА
# =========================================================

CONSENT_TEXT = (
    "<b>🔥 Добро пожаловать в Вайбометр</b>\n\n"
    "Здесь можно находить новых знакомых "
    "по интересам и общему вайбу.\n\n"
    "<b>Перед началом:</b>\n"
    "• бот только для тех, кому есть 18;\n"
    "• мы храним твою анкету и фото, чтобы показывать "
    "тебя другим пользователям;\n"
    "• фото и твой Telegram видны человеку только "
    "после взаимного вайба;\n"
    "• удалить все данные можно в любой момент: "
    "⚙️ Настройки → Удалить профиль.\n\n"
    "Нажимая «Принимаю», ты подтверждаешь, что тебе есть 18, "
    "и соглашаешься с политикой конфиденциальности (/privacy)."
)

PRIVACY_TEXT = (
    "<b>📄 ПОЛИТИКА КОНФИДЕНЦИАЛЬНОСТИ</b>\n\n"
    "<b>Что храним:</b> Telegram ID и username, имя, возраст, пол, "
    "город, интересы, текст «о себе», фото, кого ты ищешь; "
    "лайки, пропуски, блокировки, жалобы, вопросы и ответы, "
    "ответы в играх.\n\n"
    "<b>Зачем:</b> чтобы подбирать анкеты, показывать процент вайба "
    "и соединять людей после взаимного лайка. "
    "Данные не продаём и не передаём третьим лицам.\n\n"
    "<b>Кто видит:</b> другие пользователи видят анкету без фото. "
    "Фото и ссылка на твой Telegram открываются только при "
    "взаимном вайбе. Жалобы на тебя видит администратор.\n\n"
    "<b>Где хранится:</b> в базе данных бота на сервере Neon (PostgreSQL).\n\n"
    "<b>Удаление:</b> ⚙️ Настройки → Удалить профиль — "
    "анкета, фото, лайки, вопросы и игры удаляются.\n\n"
    "<b>Возраст:</b> только 18+. Анкеты младше 18 не сохраняем.\n\n"
    "Вопросы по данным — напиши администратору бота."
)


@router.message(Command("privacy"))
async def privacy_handler(message: Message):
    await message.answer(PRIVACY_TEXT)


@router.callback_query(F.data == "consent:policy")
async def consent_policy_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(PRIVACY_TEXT)


@router.callback_query(F.data == "consent:accept")
async def consent_accept_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    # Запись создаётся только после согласия
    if not await get_user(callback.from_user.id):
        await create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=callback.from_user.full_name,
        )

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.clear()
    await callback.message.answer(
        "Отлично! Давай создадим твой профиль.\n\n"
        "<b>Как тебя зовут?</b>"
    )
    await state.set_state(ProfileState.name)


# =========================================================
# START
# =========================================================

@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)

    if not user:
        await state.clear()
        await message.answer(
            CONSENT_TEXT,
            reply_markup=consent_keyboard(),
        )
        return

    profile_complete = all(
        user.get(field)
        for field in (
            "age",
            "gender",
            "city",
            "interests",
            "description",
            "photo_id",
            "search_gender",
        )
    )

    if profile_complete:
        await state.clear()
        await message.answer(
            "<b>🔥 С возвращением в Вайбометр</b>\n\n"
            "Найди людей с похожими интересами, "
            "смотри профили и проверяй совместимость.",
            reply_markup=main_menu(),
        )
        return

    current_state = await state.get_state()

    if current_state and current_state.startswith("ProfileState:"):
        await message.answer(
            "Продолжим создание профиля 👇"
        )
        return

    await state.clear()
    await message.answer(
        "<b>🔥 Давай закончим создание профиля</b>\n\n"
        "<b>Как тебя зовут?</b>"
    )
    await state.set_state(ProfileState.name)

# =========================================================
# СОЗДАНИЕ ПРОФИЛЯ
# =========================================================

@router.message(F.text == "❌ Отменить")
async def cancel_edit(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "✅ Редактирование отменено.",
        reply_markup=main_menu(),
    )

@router.message(ProfileState.name)
async def profile_name(message: Message, state: FSMContext):
    name = message.text.strip()

    if not valid_name(name):
        await message.answer(
            "❌ Имя должно быть от 2 до 50 символов.\n\n"
            "Попробуй ещё раз:"
        )
        return

    await state.update_data(name=name)

    await message.answer(
        "<b>Сколько тебе лет?</b>"
    )

    await state.set_state(ProfileState.age)


@router.message(ProfileState.age, F.text)
async def profile_age(message: Message, state: FSMContext):
    age_text = message.text.strip()

    age_digits = "".join(
        char for char in age_text
        if char.isdigit()
    )

    if not age_digits:
        await message.answer(
            "❌ Возраст нужно написать числом.\n\n"
            "Например: 18"
        )
        return

    age = int(age_digits)

    if age < MIN_AGE:
        # Анкету младше 18 не сохраняем
        await state.clear()
        await delete_user(message.from_user.id)
        await message.answer(
            "Извини, Вайбометр только для тех, кому есть 18. "
            "Твои данные мы не сохранили.\n\n"
            "Будем рады видеть тебя, когда исполнится 18 💜"
        )
        return

    if age > MAX_AGE:
        await message.answer(
            f"❌ Укажи настоящий возраст числом, до {MAX_AGE}."
        )
        return

    await state.update_data(age=age)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👦 Парень",
                    callback_data="gender:male",
                ),
                InlineKeyboardButton(
                    text="👧 Девушка",
                    callback_data="gender:female",
                ),
            ]
        ]
    )

    await message.answer(
        "<b>Отлично!</b>\n\n"
        "Теперь укажи свой пол:",
        reply_markup=keyboard,
    )

@router.callback_query(F.data.startswith("gender:"))
async def profile_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split(":")[1]

    if gender not in ("male", "female"):
        await callback.answer("Ошибка")
        return

    await state.update_data(gender=gender)

    await callback.message.edit_text(
        "<b>📍 Отлично!</b>\n\n"
        "Теперь напиши свой город."
    )

    await state.set_state(ProfileState.city)
    await callback.answer()

@router.message(ProfileState.city)
async def profile_city(message: Message, state: FSMContext):
    city = message.text.strip()

    if not valid_city(city):
        await message.answer(
            "❌ Название города выглядит некорректно.\n\n"
            "Попробуй ещё раз:"
        )
        return

    await state.update_data(city=city)

    await message.answer(
        "<b>Напиши свои интересы.</b>\n\n"
        "Например:\n"
        "баскетбол, музыка, игры, фильмы"
    )

    await state.set_state(ProfileState.interests)

@router.message(ProfileState.interests)
async def profile_interests(message: Message, state: FSMContext):
    interests = normalize_interests(message.text)

    if not interests:
        await message.answer(
            "❌ Напиши хотя бы один интерес."
        )
        return

    await state.update_data(
        interests=interests
    )

    await message.answer(
        "<b>Расскажи немного о себе.</b>\n\n"
        "Можно написать пару предложений."
    )

    await state.set_state(ProfileState.description)

@router.message(ProfileState.description)
async def profile_description(message: Message, state: FSMContext):
    description = message.text.strip()

    if not valid_description(description):
        await message.answer(
            "❌ Максимум 500 символов."
        )
        return

    await state.update_data(
        description=description
    )

    await message.answer(
        "<b>📸 Теперь отправь свою фотографию.</b>\n\n"
        "Она будет отображаться в твоей карточке."
    )

    await state.set_state(ProfileState.photo)


@router.message(ProfileState.photo, F.photo)
async def profile_photo(message: Message, state: FSMContext):
    data = await state.get_data()

    photo_id = message.photo[-1].file_id
    gender = data.get("gender")

    if not gender:
        await message.answer(
            "❌ Не удалось определить пол.\n\n"
            "Давай выберем ещё раз:"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👦 Парень",
                        callback_data="gender:male",
                    ),
                    InlineKeyboardButton(
                        text="👧 Девушка",
                        callback_data="gender:female",
                    ),
                ]
            ]
        )

        await message.answer(
            "Кто ты?",
            reply_markup=keyboard,
        )
        return

    await update_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data["name"],
        age=data["age"],
        city=data["city"],
        interests=data["interests"],
        description=data["description"],
        photo_id=photo_id,
        gender=gender,
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👦 Парней",
                    callback_data="search_gender:male",
                ),
                InlineKeyboardButton(
                    text="👧 Девушек",
                    callback_data="search_gender:female",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👥 Всех",
                    callback_data="search_gender:all",
                ),
            ],
        ]
    )

    await message.answer(
        "<b>🔥 Профиль готов!</b>\n\n"
        "Кого хочешь видеть в поиске?",
        reply_markup=keyboard,
    )

@router.callback_query(F.data.startswith("search_gender:"))
async def profile_search_gender(
    callback: CallbackQuery,
    state: FSMContext,
):
    search_gender = callback.data.split(":")[1]

    if search_gender not in ("male", "female", "all"):
        await callback.answer("Ошибка")
        return

    await update_user(
        telegram_id=callback.from_user.id,
        search_gender=search_gender,
    )

    await state.clear()

    await callback.message.edit_text(
        "<b>🔥 Профиль готов.</b>\n\n"
        "Теперь можно искать людей с похожими интересами."
    )

    await callback.message.answer(
        "Выбирай действие 👇",
        reply_markup=main_menu(),
    )

    await callback.answer()

@router.message(ProfileState.photo)
async def profile_photo_invalid(message: Message):
    await message.answer(
        "📸 Отправь именно фотографию."
    )


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

@router.message(F.text == "🔎 Найти вайб")
async def find_vibe_handler(message: Message):
    await show_next_profile(
        message,
        message.from_user.id,
    )


@router.message(F.text == "💜 Мои вайбы")
async def my_vibes_handler(message: Message):
    likes = await get_incoming_likes(
        message.from_user.id
    )

    if not likes:
        await message.answer(
            "<b>💜 МОИ ВАЙБЫ</b>\n\n"
            "Пока новых вайбов нет.\n\n"
            "Попробуй посмотреть несколько профилей "
            "и найти людей по интересам.",
            reply_markup=main_menu(),
        )
        return

    await message.answer(
        f"<b>💜 Тебе понравились {len(likes)} "
        f"{'пользователь' if len(likes) == 1 else 'пользователя'}.</b>"
    )

    for person in likes[:10]:
        text = profile_text(person)

        await message.answer(
            text,
            reply_markup=incoming_actions(
                person["telegram_id"]
            ),
        )


@router.message(F.text == "👤 Мой профиль")
async def my_profile_handler(message: Message):
    user = await get_user(message.from_user.id)

    if not user:
        await message.answer(
            "Сначала напиши /start"
        )
        return

    await user_profile_message(
        message,
        user,
        message.from_user.id,
    )


# =========================================================
# ПРОСМОТР ПРОФИЛЕЙ
# =========================================================

@router.callback_query(F.data == "browse")
async def browse_callback(callback: CallbackQuery):
    await callback.answer()

    await show_next_profile(
        callback.message,
        callback.from_user.id,
    )

# =========================================================
# РУЧНЫЕ ВОПРОСЫ
# =========================================================

@router.callback_query(F.data.startswith("question:"))
async def question_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    person_id = int(callback.data.split(":")[1])

    if person_id == callback.from_user.id:
        await callback.answer(
            "Нельзя задать вопрос самому себе.",
            show_alert=True,
        )
        return

    person = await get_user(person_id)

    if not person:
        await callback.answer(
            "Пользователь не найден.",
            show_alert=True,
        )
        return

    await state.clear()
    await state.update_data(question_to=person_id)
    await state.set_state(QuestionState.answering)

    await callback.message.answer(
        "💬 <b>Напиши свой вопрос</b>\n\n"
        "Получатель увидит именно твой текст "
        "и сможет ответить на него.\n\n"
        "Отправь вопрос одним сообщением."
    )

    await callback.answer()


@router.message(QuestionState.answering, F.text)
async def question_text_handler(
    message: Message,
    state: FSMContext,
):
    question_text = (message.text or "").strip()

    if question_text.startswith("/"):
        await message.answer(
            "Сначала отправь текст вопроса или отмени действие."
        )
        return

    if not question_text or len(question_text) > 500:
        await message.answer(
            "Вопрос должен содержать от 1 до 500 символов. "
            "Попробуй ещё раз."
        )
        return

    data = await state.get_data()
    person_id = data.get("question_to")

    if not person_id:
        await state.clear()
        await message.answer(
            "Не удалось определить получателя. "
            "Открой анкету и попробуй снова."
        )
        return

    question_id = await send_question(
        bot=message.bot,
        from_user=message.from_user.id,
        to_user=person_id,
        text=question_text,
    )

    if question_id is None:
        await message.answer(
            "Не удалось доставить вопрос. "
            "Возможно, получатель не запускал бота."
        )
        return

    await state.clear()
    await message.answer(
        "✅ Вопрос отправлен! Когда пользователь ответит, "
        "я пришлю тебе его ответ."
    )

# =========================================================
# LIKE
# =========================================================

@router.callback_query(F.data.startswith("like:"))
async def like_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    if person_id == user_id:
        await callback.answer(
            "Нельзя поставить лайк самому себе.",
            show_alert=True,
        )
        return

    already_liked = await has_like(
        from_user=user_id,
        to_user=person_id,
    )

    if not already_liked:
        await add_like(
            from_user=user_id,
            to_user=person_id,
        )

    mutual = await has_like(
        from_user=person_id,
        to_user=user_id,
    )

    await callback.answer("💜 Вайб пойман!")

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    if mutual:
        await notify_mutual(
            callback.bot, user_id, person_id, "ВАЙБ ВЗАИМНЫЙ"
        )
        return

    await show_next_profile(callback.message, user_id)

# =========================================================
# ЖАЛОБЫ
# =========================================================

@router.callback_query(F.data.startswith("report:"))
async def report_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])

    if person_id == callback.from_user.id:
        await callback.answer()
        return

    await callback.answer()
    await callback.message.answer(
        "<b>⚠️ ЖАЛОБА</b>\n\n"
        "Что не так с этой анкетой? "
        "После жалобы ты больше её не увидишь.",
        reply_markup=report_reasons_keyboard(person_id),
    )


@router.callback_query(F.data.startswith("report_reason:"))
async def report_reason_callback(callback: CallbackQuery):
    _, person_id, code = callback.data.split(":")
    person_id = int(person_id)
    reason = REPORT_REASONS.get(code, "Другое")
    user_id = callback.from_user.id

    if person_id == user_id:
        await callback.answer()
        return

    is_new = await add_report(user_id, person_id, reason)

    await callback.answer("Спасибо, жалоба отправлена.")
    await callback.message.edit_text(
        "✅ Жалоба отправлена. Мы проверим анкету."
    )

    if is_new:
        await notify_admin_report(
            callback.bot, user_id, person_id, reason
        )

    await show_next_profile(callback.message, user_id)


async def notify_admin_report(bot, from_user, person_id, reason):
    person = await get_user(person_id)

    if not person:
        return

    total = await count_reports(person_id)

    text = (
        "<b>⚠️ НОВАЯ ЖАЛОБА</b>\n\n"
        f"Причина: <b>{esc(reason)}</b>\n"
        f"От: <code>{from_user}</code>\n"
        f"На: <code>{person_id}</code>"
        + (f" (@{esc(person['username'])})" if person["username"] else "")
        + f"\nВсего жалоб на него: <b>{total}</b>\n\n"
        + profile_text(person)
    )

    keyboard = admin_report_keyboard(person_id)

    try:
        if person["photo_id"] and len(text) <= 1024:
            await bot.send_photo(
                ADMIN_ID,
                photo=person["photo_id"],
                caption=text,
                reply_markup=keyboard,
            )
        else:
            await bot.send_message(
                ADMIN_ID, text, reply_markup=keyboard
            )
    except Exception:
        logging.exception("Не удалось отправить жалобу админу")


async def apply_ban(bot, person_id, banned):
    found = await set_banned(person_id, banned)

    if found and banned:
        try:
            await bot.send_message(person_id, BANNED_TEXT)
        except Exception:
            pass

    return found


@router.callback_query(F.data.startswith("admin_ban:"))
async def admin_ban_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return

    person_id = int(callback.data.split(":")[1])
    found = await apply_ban(callback.bot, person_id, True)

    await callback.answer("Забанен" if found else "Пользователь не найден")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"🚫 <code>{person_id}</code> забанен. Снять: /unban {person_id}"
        if found else "Пользователь уже удалён."
    )


@router.callback_query(F.data.startswith("admin_dismiss:"))
async def admin_dismiss_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return

    person_id = int(callback.data.split(":")[1])
    await dismiss_reports(person_id)

    await callback.answer("Жалобы отклонены")
    await callback.message.edit_reply_markup(reply_markup=None)


@router.message(Command("ban", "unban"))
async def admin_ban_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = (message.text or "").split()
    banned = parts[0].lstrip("/").split("@")[0] == "ban"

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Формат: /ban ID или /unban ID")
        return

    person_id = int(parts[1])
    found = await apply_ban(message.bot, person_id, banned)

    if not found:
        await message.answer("Пользователь не найден.")
    else:
        await message.answer(
            f"🚫 {person_id} забанен." if banned
            else f"✅ {person_id} разбанен."
        )


# =========================================================
# SKIP
# =========================================================

@router.callback_query(F.data.startswith("skip:"))
async def skip_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])

    await add_skip(
        from_user=callback.from_user.id,
        to_user=person_id,
    )

    await callback.answer("👎 Мимо")

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await show_next_profile(
        callback.message,
        callback.from_user.id,
    )


# =========================================================
# BLOCK
# =========================================================

@router.callback_query(F.data.startswith("block:"))
async def block_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])

    await add_block(
        from_user=callback.from_user.id,
        to_user=person_id,
    )

    await callback.answer(
        "🚫 Пользователь заблокирован."
    )

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    await show_next_profile(
        callback.message,
        callback.from_user.id,
    )


# =========================================================
# ВХОДЯЩИЙ ВАЙБ
# =========================================================

@router.callback_query(F.data.startswith("incoming_like:"))
async def incoming_like_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    await add_like(
        from_user=user_id,
        to_user=person_id,
    )

    mutual = await has_like(
        from_user=person_id,
        to_user=user_id,
    )

    await callback.answer("💜")

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    if mutual:
        await notify_mutual(
            callback.bot, user_id, person_id, "ВАЙБ ВЗАИМНЫЙ"
        )


@router.callback_query(F.data.startswith("incoming_skip:"))
async def incoming_skip_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])

    await add_skip(
        from_user=callback.from_user.id,
        to_user=person_id,
    )

    await callback.answer("👎 Мимо")

    await callback.message.edit_reply_markup(
        reply_markup=None
    )


# =========================================================
# ПОЗНАКОМИТЬСЯ
# =========================================================

@router.callback_query(F.data.startswith("contact:"))
async def contact_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])

    user_id = callback.from_user.id
    person = await get_user(person_id)

    if not person:
        await callback.answer(
            "Пользователь не найден.",
            show_alert=True,
        )
        return

    # Контакт открывается только при взаимном вайбе
    mutual = (
        await has_like(from_user=user_id, to_user=person_id)
        and await has_like(from_user=person_id, to_user=user_id)
    )

    if not mutual:
        await callback.answer(
            "Контакт откроется после взаимного вайба.",
            show_alert=True,
        )
        return

    await callback.answer()

    username = person["username"]

    if username:
        username = username.lstrip("@")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 Открыть профиль",
                        url=f"https://t.me/{username}",
                    )
                ]
            ]
        )

        await callback.message.answer(
            "<b>💬 Можно начинать общение.</b>\n\n"
            f"Telegram: @{esc(username)}",
            reply_markup=keyboard,
        )
    else:
        await callback.message.answer(
            "<b>💬 Можно начинать общение.</b>\n\n"
            "У пользователя пока нет username в Telegram."
        )


# =========================================================
# СТАТИСТИКА
# =========================================================

@router.message(F.text == "📊 Статистика")
async def statistics_handler(message: Message):
    user = await get_user(message.from_user.id)

    if not user:
        await message.answer(
            "Сначала напиши /start"
        )
        return

    try:
        from database import get_stats

        stats = await get_stats(
            message.from_user.id
        )

        text = (
            "<b>📊 ТВОЯ СТАТИСТИКА</b>\n\n"
            f"👀 Просмотров: {stats.get('views', 0)}\n"
            f"💜 Лайков: {stats.get('likes', 0)}\n"
            f"🤝 Взаимных вайбов: "
            f"{stats.get('mutual_likes', 0)}"
        )

    except Exception:
        text = (
            "<b>📊 ТВОЯ СТАТИСТИКА</b>\n\n"
            "Статистика пока собирается.\n"
            "Основные показатели появятся после активности."
        )

    await message.answer(
        text,
        reply_markup=stats_keyboard(),
    )


# =========================================================
# НАСТРОЙКИ
# =========================================================

@router.message(F.text == "⚙️ Настройки")
async def settings_handler(message: Message):
    await message.answer(
        "<b>⚙️ НАСТРОЙКИ</b>\n\n"
        "Здесь можно изменить данные профиля.",
        reply_markup=settings_keyboard(),
    )


@router.callback_query(F.data == "edit_profile")
async def edit_profile_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    await callback.message.answer(
        "<b>✏️ РЕДАКТИРОВАНИЕ ПРОФИЛЯ</b>\n\n"
        "Как тебя зовут?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="❌ Отменить")
                ]
            ],
            resize_keyboard=True,
        ),
    )

    await state.set_state(ProfileState.name)


# =========================================================
# УДАЛЕНИЕ ПРОФИЛЯ
# =========================================================

@router.callback_query(F.data == "delete_profile")
async def delete_profile_callback(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Да, удалить",
                    callback_data="delete_confirm",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Отмена",
                    callback_data="main_menu",
                )
            ],
        ]
    )

    await callback.answer()

    await callback.message.answer(
        "<b>⚠️ УДАЛИТЬ ПРОФИЛЬ?</b>\n\n"
        "Все данные профиля будут удалены.",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "delete_confirm")
async def delete_confirm_callback(callback: CallbackQuery):
    try:
        from database import delete_user

        await delete_user(
            callback.from_user.id
        )

        await callback.answer(
            "Профиль удалён."
        )

        await callback.message.answer(
            "<b>🗑 ПРОФИЛЬ УДАЛЁН</b>\n\n"
            "Если захочешь вернуться — нажми /start"
        )

    except Exception:
        await callback.answer(
            "Не удалось удалить профиль.",
            show_alert=True,
        )


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        "<b>🏠 ГЛАВНОЕ МЕНЮ</b>",
        reply_markup=main_menu(),
    )


# =========================================================
# ВАЙБ-ИГРЫ
# =========================================================

@router.message(F.text == "🎮 Вайб-игры")
async def vibe_games_handler(message: Message):
    user_id = message.from_user.id

    user = await get_user(user_id)

    if not user or not is_adult(user["age"]):
        await message.answer(
            "Сначала создай профиль через /start."
        )
        return

    # Убираем пользователя из старой очереди
    waiting_players[:] = [
        x for x in waiting_players
        if x != user_id
    ]

    opponent_id = None

    for candidate_id in waiting_players:
        candidate = await get_user(candidate_id)

        if candidate and is_adult(candidate["age"]):
            opponent_id = candidate_id
            break

    if opponent_id is None:
        waiting_players.append(user_id)

        await message.answer(
            "<b>🎮 ВАЙБ-ИГРА</b>\n\n"
            "Ищем тебе соперника...\n\n"
            "Как только появится другой игрок — "
            "начнётся игра.",
            reply_markup=main_menu(),
        )
        return

    waiting_players.remove(opponent_id)

    game = await start_game(
        opponent_id,
        user_id,
    )

    await message.answer(
        "<b>🎮 СОПЕРНИК НАЙДЕН</b>\n\n"
        "Вам обоим предстоит ответить "
        "на 5 вопросов.\n\n"
        "В конце увидите процент совпадений.",
        reply_markup=game_actions(game["id"]),
    )

    try:
        await message.bot.send_message(
            opponent_id,
            "<b>🎮 СОПЕРНИК НАЙДЕН</b>\n\n"
            "Вам обоим предстоит ответить "
            "на 5 вопросов.\n\n"
            "Готов начать?",
            reply_markup=game_actions(game["id"]),
        )
    except Exception:
        pass


# =========================================================
# СТАРТ ИГРЫ
# =========================================================

@router.callback_query(F.data.startswith("game_start:"))
async def game_start_callback(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    # Сначала проверяем: это уже созданная игра?
    question = await get_current_question(
        target_id,
        user_id,
    )

    if question:
        await callback.answer()

        await callback.message.answer(
            f"<b>🎮 ВОПРОС "
            f"{question['index'] + 1}/5</b>\n\n"
            f"{esc(question['question'])}",
            reply_markup=game_keyboard(
                target_id,
                question["index"],
                question["a"],
                question["b"],
            ),
        )
        return

    # Иначе считаем, что это ID пользователя
    opponent = await get_user(target_id)
    user = await get_user(user_id)

    if not opponent or not user:
        await callback.answer(
            "Пользователь не найден.",
            show_alert=True,
        )
        return

    if not is_adult(user["age"]) or not is_adult(opponent["age"]):
        await callback.answer(
            "Сначала нужно заполнить профиль.",
            show_alert=True,
        )
        return

    game = await start_game(user_id, target_id)
    game_id = game["id"]

    await callback.answer("Игра создана!")

    question = await get_current_question(
        game_id,
        user_id,
    )

    if question:
        await callback.message.answer(
            "<b>🎮 ВАЙБ-ИГРА</b>\n\n"
            f"<b>ВОПРОС 1/5</b>\n\n"
            f"{esc(question['question'])}",
            reply_markup=game_keyboard(
                game_id,
                question["index"],
                question["a"],
                question["b"],
            ),
        )

    try:
        await callback.bot.send_message(
            target_id,
            "<b>🎮 ТЕБЯ ПРИГЛАСИЛИ В ВАЙБ-ИГРУ</b>\n\n"
            "Нажми кнопку, чтобы ответить на первый вопрос.",
            reply_markup=game_actions(game_id),
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("game_answer:"))
async def game_answer_callback(callback: CallbackQuery):
    parts = callback.data.split(":")

    game_id = int(parts[1])
    question_index = int(parts[2])
    answer = parts[3]

    user_id = callback.from_user.id

    success = await save_answer(
        game_id,
        user_id,
        question_index,
        answer,
    )

    if not success:
        await callback.answer(
            "Этот вопрос уже отвечен.",
            show_alert=True,
        )
        return

    await callback.answer("Ответ принят!")

    next_question = await get_current_question(
        game_id,
        user_id,
    )

    if next_question:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        await callback.message.answer(
            f"<b>🎮 ВОПРОС "
            f"{next_question['index'] + 1}/5</b>\n\n"
            f"{esc(next_question['question'])}",
            reply_markup=game_keyboard(
                game_id,
                next_question["index"],
                next_question["a"],
                next_question["b"],
            ),
        )

        return

    result = await complete_game(game_id)

    if not result:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )

        await callback.message.answer(
            "<b>✅ ВСЕ ОТВЕТЫ ГОТОВЫ</b>\n\n"
            "Ждём второго игрока."
        )

        return

    await callback.message.edit_reply_markup(
        reply_markup=None
    )

    text = get_result_text(
        result["matches"],
        result["percentage"],
    )

    opponent_id = (
        result["user_two"]
        if result["user_one"] == user_id
        else result["user_one"]
    )

    await callback.message.answer(
        text,
        reply_markup=game_result_actions(
            opponent_id
        ),
    )

    try:
        await callback.bot.send_message(
            opponent_id,
            text,
            reply_markup=game_result_actions(
                user_id
            ),
        )
    except Exception:
        pass


# =========================================================
# ВАЙБ ПОСЛЕ ИГРЫ
# =========================================================

@router.callback_query(F.data.startswith("game_like:"))
async def game_like_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    await add_like(
        from_user=user_id,
        to_user=person_id,
    )

    mutual = await has_like(
        from_user=person_id,
        to_user=user_id,
    )

    if mutual:
        await callback.answer(
            "💜 Вайб взаимный!"
        )

        await notify_mutual(
            callback.bot, user_id, person_id, "ВАЙБ ПОСЛЕ ИГРЫ ВЗАИМНЫЙ"
        )

    else:
        await callback.answer(
            "💜 Вайб отправлен!"
        )


# =========================================================
# ОТВЕТЫ НА ВОПРОСЫ
# =========================================================

@router.message(F.text)
async def universal_text_handler(
    message: Message,
    state: FSMContext,
):
    current_state = await state.get_state()

    # Если пользователь сейчас заполняет профиль,
    # этот обработчик ничего не делает.
    if current_state is not None:
        return

    try:
        from database import get_pending_questions

        pending = await get_pending_questions(
            message.from_user.id
        )

        if not pending:
            return

        question = pending[0]

        success = await submit_answer(
            message.bot,
            question["id"],
            message.text,
        )

        if success:
            await message.answer(
                "<b>✅ Ответ отправлен.</b>",
                reply_markup=main_menu(),
            )

    except Exception:
        return

@router.callback_query(F.data == "achievements")
async def achievements_callback(callback: CallbackQuery):
    await callback.answer()

    stats = await get_stats(callback.from_user.id)

    if not stats:
        stats = {}

    likes = stats.get("likes", 0)
    mutual = stats.get("mutual", 0)
    questions = stats.get("questions", 0)
    games = stats.get("games", 0)

    text = (
        "<b>🏆 ТВОИ ДОСТИЖЕНИЯ</b>\n\n"
        f"{'✅' if likes >= 1 else '🔒'} Первый вайб — {likes >= 1}\n"
        f"{'✅' if mutual >= 1 else '🔒'} Взаимность — {mutual >= 1}\n"
        f"{'✅' if questions >= 1 else '🔒'} Первое общение — {questions >= 1}\n"
        f"{'✅' if games >= 1 else '🔒'} Первая игра — {games >= 1}"
    )

    await callback.message.answer(text)


@router.callback_query(F.data == "streak")
async def streak_callback(callback: CallbackQuery):
    await callback.answer(
        "🔥 Серия активности пока не реализована.",
        show_alert=True,
    )

@router.callback_query(F.data == "blocked_users")
async def blocked_users_callback(callback: CallbackQuery):
    await callback.answer()

    blocked = await get_blocked_users(callback.from_user.id)

    if not blocked:
        await callback.message.answer(
            "🚫 <b>Заблокированные пользователи</b>\n\n"
            "Список пока пуст."
        )
        return

    text = ["🚫 <b>ЗАБЛОКИРОВАННЫЕ ПОЛЬЗОВАТЕЛИ</b>\n"]

    for person in blocked:
        name = person["full_name"] or "Без имени"
        age = person["age"] or "—"
        city = person["city"] or "—"

        text.append(
            f"• {name} — {age} лет, {city}"
        )

    await callback.message.answer("\n".join(text))