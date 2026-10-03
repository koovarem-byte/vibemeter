from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from database import (
    create_user,
    get_user,
    update_user,
    get_candidates,
    add_like,
    has_like,
    add_skip,
    add_block,
    get_incoming_likes,
    add_question,
    get_question,
    answer_question,
    get_pending_questions,
    get_stats,
)

from keyboards import (
    main_menu,
    after_profile,
    profile_actions,
    incoming_actions,
)

from states import (
    ProfileState,
    QuestionState,
    GameState,
)

from questions import (
    send_question,
    submit_answer,
)

from games import (
    start_game,
    get_current_question,
    save_answer,
    get_progress,
    complete_game,
    get_result_text,
)

from utils import (
    get_common_interests,
    format_common_interests,
    valid_name,
    valid_age,
    valid_city,
    valid_description,
)


router = Router()

current_profile = {}
waiting_players = []


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

async def show_next_profile(
    message: Message,
    user_id: int,
):
    candidates = await get_candidates(user_id)

    if not candidates:
        await message.answer(
            "<b>🔎 Пока никого нового нет</b>\n\n"
            "Попробуй зайти чуть позже.",
        )
        return

    person = candidates[0]

    current_profile[user_id] = person["telegram_id"]

    current_user = await get_user(user_id)

    common = []

    if current_user:
        common = get_common_interests(
            current_user["interests"] or "",
            person["interests"] or "",
        )

    text = (
        f"<b>👤 {person['full_name'] or 'Без имени'}</b>\n\n"
        f"<b>Возраст:</b> {person['age']}\n"
        f"<b>Город:</b> {person['city'] or 'не указан'}\n\n"
        f"<b>Интересы:</b>\n"
        f"{person['interests'] or 'не указаны'}\n\n"
        f"<b>О себе:</b>\n"
        f"{person['description'] or 'ничего не рассказал'}"
    )

    if common:
        text += (
            "\n\n"
            "<b>🔥 Общие интересы:</b>\n"
            f"{format_common_interests(common)}"
        )

    if person["photo_id"]:
        await message.answer_photo(
            person["photo_id"],
            caption=text,
            reply_markup=profile_actions(),
        )
    else:
        await message.answer(
            text,
            reply_markup=profile_actions(),
        )


# =========================================================
# START
# =========================================================

@router.message(F.text == "/start")
async def start_handler(
    message: Message,
    state: FSMContext,
):
    user = await get_user(message.from_user.id)

    if not user:
        await create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

        await message.answer(
            "<b>👋 Добро пожаловать в Вайбометр</b>\n\n"
            "Здесь можно находить людей с похожими интересами,\n"
            "смотреть профили и играть в вайб-игры.\n\n"
            "Давай создадим профиль."
        )

        await message.answer(
            "Как тебя зовут?"
        )

        await state.set_state(
            ProfileState.name
        )

        return

    if not user["age"]:
        await message.answer(
            "<b>Давай закончим создание профиля.</b>\n\n"
            "Как тебя зовут?"
        )

        await state.set_state(
            ProfileState.name
        )

        return

    await message.answer(
        "<b>С возвращением 👋</b>\n\n"
        "Что делаем?",
        reply_markup=main_menu(),
    )


# =========================================================
# СОЗДАНИЕ ПРОФИЛЯ
# =========================================================

@router.message(ProfileState.name)
async def profile_name(
    message: Message,
    state: FSMContext,
):
    name = (message.text or "").strip()

    if not valid_name(name):
        await message.answer(
            "Имя должно быть от 2 до 50 символов."
        )
        return

    await state.update_data(
        name=name
    )

    await message.answer(
        "Сколько тебе лет?"
    )

    await state.set_state(
        ProfileState.age
    )


@router.message(ProfileState.age)
async def profile_age(
    message: Message,
    state: FSMContext,
):
    age = (message.text or "").strip()

    if not valid_age(age):
        await message.answer(
            "Укажи возраст числом от 16 до 99."
        )
        return

    await state.update_data(
        age=int(age)
    )

    await message.answer(
        "Из какого ты города?"
    )

    await state.set_state(
        ProfileState.city
    )


@router.message(ProfileState.city)
async def profile_city(
    message: Message,
    state: FSMContext,
):
    city = (message.text or "").strip()

    if not valid_city(city):
        await message.answer(
            "Напиши нормальное название города."
        )
        return

    await state.update_data(
        city=city
    )

    await message.answer(
        "Напиши несколько своих интересов.\n\n"
        "Например:\n"
        "баскетбол, музыка, игры, кино"
    )

    await state.set_state(
        ProfileState.interests
    )


@router.message(ProfileState.interests)
async def profile_interests(
    message: Message,
    state: FSMContext,
):
    interests = (message.text or "").strip()

    if not interests:
        await message.answer(
            "Напиши хотя бы один интерес."
        )
        return

    await state.update_data(
        interests=interests
    )

    await message.answer(
        "Расскажи немного о себе.\n\n"
        "До 500 символов."
    )

    await state.set_state(
        ProfileState.description
    )


@router.message(ProfileState.description)
async def profile_description(
    message: Message,
    state: FSMContext,
):
    description = (message.text or "").strip()

    if not valid_description(description):
        await message.answer(
            "Описание должно быть от 1 до 500 символов."
        )
        return

    await state.update_data(
        description=description
    )

    await message.answer(
        "Теперь отправь свою фотографию 📸"
    )

    await state.set_state(
        ProfileState.photo
    )


@router.message(ProfileState.photo)
async def profile_photo(
    message: Message,
    state: FSMContext,
):
    if not message.photo:
        await message.answer(
            "Отправь именно фотографию 📸"
        )
        return

    data = await state.get_data()

    photo_id = message.photo[-1].file_id

    await update_user(
        message.from_user.id,
        full_name=data["name"],
        age=data["age"],
        city=data["city"],
        interests=data["interests"],
        description=data["description"],
        photo_id=photo_id,
        username=message.from_user.username,
    )

    await state.clear()

    await message.answer(
        "<b>✅ Профиль готов</b>\n\n"
        "Теперь можно смотреть людей и искать свой вайб.",
        reply_markup=after_profile(),
    )


# =========================================================
# МОЙ ПРОФИЛЬ
# =========================================================

@router.message(F.text == "👤 Мой профиль")
async def my_profile_handler(
    message: Message,
):
    user = await get_user(
        message.from_user.id
    )

    if not user or not user["age"]:
        await message.answer(
            "Сначала создай профиль 👤"
        )
        return

    text = (
        f"<b>👤 {user['full_name']}</b>\n\n"
        f"<b>Возраст:</b> {user['age']}\n"
        f"<b>Город:</b> {user['city'] or 'не указан'}\n\n"
        f"<b>Интересы:</b>\n"
        f"{user['interests'] or 'не указаны'}\n\n"
        f"<b>О себе:</b>\n"
        f"{user['description'] or 'не указано'}"
    )
    if user["photo_id"]:
        await message.answer_photo(
            user["photo_id"],
            caption=text,
        )
    else:
        await message.answer(
            text
        )

    # =========================================================
    # ПРОСМОТР ПРОФИЛЕЙ
    # =========================================================

    @router.message(F.text == "🔎 Проверить вайб")
    async def browse_handler(
            message: Message,
    ):
        user = await get_user(
            message.from_user.id
        )

        if not user or not user["age"]:
            await message.answer(
                "Сначала создай профиль 👤"
            )
            return

        await show_next_profile(
            message,
            message.from_user.id,
        )

    # =========================================================
    # ВАЙБ / МИМО / БЛОК
    # =========================================================

    @router.callback_query(F.data == "like")
    async def like_handler(
            callback: CallbackQuery,
    ):
        user_id = callback.from_user.id

        person_id = current_profile.get(user_id)

        if not person_id:
            await callback.answer(
                "Профиль уже закончился",
                show_alert=True,
            )
            return

        await callback.answer(
            "💜 Вайб отправлен"
        )

        await add_like(
            user_id,
            person_id,
        )

        mutual = await has_like(
            person_id,
            user_id,
        )

        try:
            await callback.message.delete()
        except Exception:
            pass

        if mutual:
            person = await get_user(person_id)

            username = person["username"] if person else None

            if username:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="💬 Общаться",
                                url=f"https://t.me/{username.lstrip('@')}",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="🔎 Смотреть дальше",
                                callback_data="browse",
                            )
                        ],
                    ]
                )
            else:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="🔎 Смотреть дальше",
                                callback_data="browse",
                            )
                        ]
                    ]
                )

            await callback.bot.send_message(
                user_id,
                "<b>💜 ВЗАИМНЫЙ ВАЙБ</b>\n\n"
                "Вы понравились друг другу.",
                reply_markup=keyboard,
            )

            try:
                await callback.bot.send_message(
                    person_id,
                    "<b>💜 ВЗАИМНЫЙ ВАЙБ</b>\n\n"
                    "Вы понравились друг другу.",
                )
            except Exception:
                pass

        else:
            await show_next_profile(
                callback.message,
                user_id,
            )

    @router.callback_query(F.data == "skip")
    async def skip_handler(
            callback: CallbackQuery,
    ):
        user_id = callback.from_user.id

        person_id = current_profile.get(user_id)

        if not person_id:
            await callback.answer(
                "Профиль уже закончился",
                show_alert=True,
            )
            return

        await add_skip(
            user_id,
            person_id,
        )

        await callback.answer(
            "👎 Пропущено"
        )

        try:
            await callback.message.delete()
        except Exception:
            pass

        await show_next_profile(
            callback.message,
            user_id,
        )

    @router.callback_query(F.data == "block")
    async def block_handler(
            callback: CallbackQuery,
    ):
        user_id = callback.from_user.id

        person_id = current_profile.get(user_id)

        if not person_id:
            await callback.answer(
                "Профиль уже закончился",
                show_alert=True,
            )
            return

        await add_block(
            user_id,
            person_id,
        )
        await callback.answer(
            "🚫 Пользователь заблокирован"
        )

        try:
            await callback.message.delete()
        except Exception:
            pass

        await show_next_profile(
            callback.message,
            user_id,
        )

    # =========================================================
    # ВХОДЯЩИЕ ВАЙБЫ
    # =========================================================

    @router.message(F.text == "👀 Кто поймал мой вайб")
    async def incoming_handler(
            message: Message,
    ):
        users = await get_incoming_likes(
            message.from_user.id
        )

        if not users:
            await message.answer(
                "<b>👀 Пока никто не поймал твой вайб</b>\n\n"
                "Продолжай смотреть профили."
            )
            return

        for person in users[:10]:

            text = (
                f"<b>👀 {person['full_name'] or 'Без имени'}</b>\n\n"
                f"<b>Возраст:</b> {person['age']}\n"
                f"<b>Город:</b> {person['city'] or 'не указан'}\n\n"
                f"<b>Интересы:</b>\n"
                f"{person['interests'] or 'не указаны'}\n\n"
                f"<b>О себе:</b>\n"
                f"{person['description'] or 'не указано'}"
            )

            keyboard = incoming_actions(
                person["telegram_id"]
            )

            if person["photo_id"]:
                await message.answer_photo(
                    person["photo_id"],
                    caption=text,
                    reply_markup=keyboard,
                )
            else:
                await message.answer(
                    text,
                    reply_markup=keyboard,
                )

    @router.callback_query(
        F.data.startswith("incoming_like:")
    )
    async def incoming_like_handler(
            callback: CallbackQuery,
    ):
        person_id = int(
            callback.data.split(":")[1]
        )

        user_id = callback.from_user.id

        await add_like(
            user_id,
            person_id,
        )

        await callback.answer(
            "💜 Вайб отправлен"
        )

        mutual = await has_like(
            person_id,
            user_id,
        )

        try:
            await callback.message.delete()
        except Exception:
            pass

        if mutual:
            person = await get_user(
                person_id
            )

            if person and person["username"]:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="💬 Общаться",
                                url=(
                                    "https://t.me/"
                                    f"{person['username'].lstrip('@')}"
                                ),
                            )
                        ]
                    ]
                )
            else:
                keyboard = None

            await callback.message.answer(
                "<b>💜 ВЗАИМНЫЙ ВАЙБ</b>\n\n"
                "Вы понравились друг другу.",
                reply_markup=keyboard,
            )

            try:
                await callback.bot.send_message(
                    person_id,
                    "<b>💜 ВЗАИМНЫЙ ВАЙБ</b>\n\n"
                    "Вы понравились друг другу.",
                )
            except Exception:
                pass

    @router.callback_query(
        F.data.startswith("incoming_skip:")
    )
    async def incoming_skip_handler(
            callback: CallbackQuery,
    ):
        person_id = int(
            callback.data.split(":")[1]
        )

        await add_skip(
            callback.from_user.id,
            person_id,
        )

        await callback.answer(
            "👎 Мимо"
        )

        try:
            await callback.message.delete()
        except Exception:
            pass

    # =========================================================
    # ВОПРОСЫ
    # =========================================================

    @router.callback_query(F.data == "question")
    async def question_handler(
            callback: CallbackQuery,
            state: FSMContext,
    ):
        user_id = callback.from_user.id

        person_id = current_profile.get(
            user_id
        )

        if not person_id:
            await callback.answer(
                "Профиль уже недоступен",
                show_alert=True,
            )
            return
        question_id = await send_question(
            callback.bot,
            user_id,
            person_id,
        )

        if not question_id:
            await callback.answer(
                "Не удалось отправить вопрос",
                show_alert=True,
            )
            return

        await state.set_state(
            QuestionState.answering
        )

        await state.update_data(
            question_id=question_id
        )

        await callback.answer(
            "💬 Вопрос отправлен"
        )

    @router.message(QuestionState.answering)
    async def question_answer_handler(
            message: Message,
            state: FSMContext,
    ):
        data = await state.get_data()

        question_id = data.get(
            "question_id"
        )

        if not question_id:
            await state.clear()
            return

        answer = message.text or ""

        success = await submit_answer(
            message.bot,
            question_id,
            answer,
        )

        if not success:
            await message.answer(
                "Не получилось отправить ответ."
            )
            return

        await state.clear()

        await message.answer(
            "✅ Ответ отправлен.",
            reply_markup=after_profile(),
        )

    # =========================================================
    # СТАТИСТИКА
    # =========================================================

    @router.message(F.text == "📊 Статистика")
    async def stats_handler(
            message: Message,
    ):
        stats = await get_stats(
            message.from_user.id
        )

        await message.answer(
            "<b>📊 ТВОЯ СТАТИСТИКА</b>\n\n"
            f"💜 Вайбов отправлено: "
            f"{stats['likes_sent']}\n"
            f"💜 Вайбов получено: "
            f"{stats['likes_received']}\n"
            f"👎 Мимо: "
            f"{stats['skips']}\n"
            f"🚫 Блокировок: "
            f"{stats['blocks']}\n"
            f"💬 Вопросов получено: "
            f"{stats['questions_received']}"
        )

    # =========================================================
    # ИГРА
    # =========================================================

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
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=answer_b,
                        callback_data=(
                            f"game_answer:"
                            f"{game_id}:"
                            f"{question_index}:b"
                        ),
                    )
                ],
            ]
        )

    def game_result_keyboard(person):
        buttons = []

        if person and person["username"]:
            buttons.append(
                [
                    InlineKeyboardButton(
                        text="💬 Общаться",
                        url=(
                            "https://t.me/"
                            f"{person['username'].lstrip('@')}"
                        ),
                    )
                ]
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    text="🔎 Смотреть дальше",
                    callback_data="browse",
                )
            ]
        )

        return InlineKeyboardMarkup(
            inline_keyboard=buttons
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
                    callback_data=f"game_answer:{game_id}:{question_index}:a",
                )
            ],
            [
                InlineKeyboardButton(
                    text=answer_b,
                    callback_data=f"game_answer:{game_id}:{question_index}:b",
                )
            ],
        ]
    )

async def send_game_question(
    bot,
    user_id: int,
    game_id: int,
):
    question = await get_current_question(
        game_id,
        user_id,
    )

    if not question:
        return

    text = (
        "<b>🎮 ВАЙБ-ИГРА</b>\n\n"
        f"<b>Вопрос {question['index'] + 1}/5</b>\n\n"
        f"{question['question']}\n\n"
        "Выбери свой вариант 👇"
    )

    await bot.send_message(
        user_id,
        text,
        reply_markup=game_keyboard(
            game_id,
            question["index"],
            question["a"],
            question["b"],
        ),
    )