import html
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
    get_blocked_users
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
)

from states import ProfileState
from utils import (
    normalize_interests,
    get_common_interests,
    format_common_interests,
    valid_name,
    valid_age,
    valid_city,
    valid_description,
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

    # Дополнительная проверка пола и возрастной группы
    viewer_age = viewer.get("age") or 0
    viewer_gender = viewer.get("search_gender") or "all"

    filtered = []

    for person in candidates:
        person_id = person.get("telegram_id")
        person_age = person.get("age") or 0

        if person_id == user_id:
            continue

        # Не показываем несовместимую возрастную группу
        if (viewer_age < 18 and person_age >= 18) or (
            viewer_age >= 18 and person_age < 18
        ):
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


# =========================================================
# START
# =========================================================

@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    user = await get_user(message.from_user.id)

    if not user:
        await create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

        await state.clear()
        await message.answer(
            "<b>🔥 Добро пожаловать в Вайбометр</b>\n\n"
            "Здесь можно находить новых знакомых "
            "по интересам и общему вайбу.\n\n"
            "Сначала давай создадим твой профиль.\n\n"
            "<b>Как тебя зовут?</b>"
        )
        await state.set_state(ProfileState.name)
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

    if age < 16 or age > 99:
        await message.answer(
            "❌ Укажи возраст от 16 до 99 лет."
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

@router.callback_query(F.data.startswith("contact:"))
async def contact_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])
    person = await get_user(person_id)

    await callback.answer()

    if not person:
        await callback.message.answer(
            "Пользователь больше недоступен."
        )
        return

    username = person.get("username")

    if username:
        await callback.message.answer(
            "💬 <b>Переходи в Telegram и знакомься!</b>\n\n"
            f'<a href="https://t.me/{esc(username)}">'
            "Открыть профиль пользователя</a>"
        )
    else:
        await callback.message.answer(
            "У пользователя не указан публичный Telegram username.\n\n"
            "Попроси его указать username в Telegram, "
            "чтобы можно было перейти в личные сообщения."
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
        await callback.message.answer(
            "<b>💜 ВАЙБ ВЗАИМНЫЙ</b>\n\n"
            "Вы оба выбрали друг друга.\n\n"
            "Нажми «Познакомиться», чтобы перейти "
            "в Telegram, или смотри дальше.",
            reply_markup=mutual_actions(person_id),
        )

        try:
            await callback.bot.send_message(
                person_id,
                "<b>💜 ВАЙБ ВЗАИМНЫЙ</b>\n\n"
                "Вы оба выбрали друг друга!",
                reply_markup=mutual_actions(user_id),
            )
        except Exception:
            pass

        return

    await show_next_profile(callback.message, user_id)
    
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
        await callback.message.answer(
            "<b>💜 ВАЙБ ВЗАИМНЫЙ</b>\n\n"
            "Теперь вы можете начать общение.",
            reply_markup=mutual_actions(person_id),
        )

        try:
            await callback.bot.send_message(
                person_id,
                "<b>💜 ВАЙБ ВЗАИМНЫЙ</b>\n\n"
                "У вас появился новый взаимный вайб.",
                reply_markup=mutual_actions(user_id),
            )
        except Exception:
            pass


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
# ЗАДАТЬ ВОПРОС
# =========================================================

@router.callback_query(F.data.startswith("question:"))
async def question_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])

    question_id = await send_question(
        callback.bot,
        callback.from_user.id,
        person_id,
    )

    if question_id:
        await callback.answer(
            "💬 Вопрос отправлен!"
        )
    else:
        await callback.answer(
            "Не удалось отправить вопрос.",
            show_alert=True,
        )


# =========================================================
# ТЕМЫ ДЛЯ ОБЩЕНИЯ
# =========================================================


# =========================================================
# ПОЗНАКОМИТЬСЯ
# =========================================================

@router.callback_query(F.data.startswith("contact:"))
async def contact_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])

    person = await get_user(person_id)

    if not person:
        await callback.answer(
            "Пользователь не найден.",
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

    if not user:
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

        if not candidate:
            continue

        if (
            (user["age"] < 18 and candidate["age"] < 18)
            or
            (user["age"] >= 18 and candidate["age"] >= 18)
        ):
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

    if (
        (user["age"] < 18 and opponent["age"] >= 18)
        or
        (user["age"] >= 18 and opponent["age"] < 18)
    ):
        await callback.answer(
            "Играть можно только в своей возрастной группе.",
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

        await callback.message.answer(
            "<b>💜 ВАЙБ ВЗАИМНЫЙ</b>\n\n"
            "Теперь можете начать общение.",
            reply_markup=mutual_actions(person_id),
        )

        try:
            await callback.bot.send_message(
                person_id,
                "<b>💜 ВАЙБ ВЗАИМНЫЙ</b>\n\n"
                "После игры у вас появился взаимный вайб.",
                reply_markup=mutual_actions(user_id),
            )
        except Exception:
            pass

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