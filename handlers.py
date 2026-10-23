import html
import re
import logging
import random
import time

from aiogram import Router, F
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
)

import ui
import vibehour
import citygoal
import boost
import weeklystats
import ratelimit
import admin
from database import (
    is_blocked,
    add_referral,
    get_vibe_test,
    add_start_source,
    source_stats,
    set_vibe_hour_notify,
    count_referrals,
    get_inviter,
    create_user,
    get_user,
    update_user,
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
    set_banned,
    dismiss_reports,
    touch_user,
)
from keyboards import (
    main_menu,
    open_app_keyboard,
    cancel_keyboard,
    profile_actions,
    incoming_actions,
    mutual_actions,
    contact_keyboard,
    liked_you_keyboard,
    gender_keyboard,
    search_gender_keyboard,
    consent_keyboard,
    settings_keyboard,
    delete_confirm_keyboard,
    stats_keyboard,
    game_keyboard,
    game_result_actions,
    story_button,
    vibe_hour_on_keyboard,
    question_answer_keyboard,
    report_reasons_keyboard,
)
from config import ADMIN_ID
from states import ProfileState, QuestionState
from utils import (
    normalize_interests,
    get_common_interests,
    valid_name,
    valid_city,
    valid_description,
    is_adult,
    MIN_AGE,
    MAX_AGE,
)
from questions import send_question, submit_answer, get_question_data
from database import get_game
from games import (
    game_queue,
    calculate_result,
    start_game,
    get_current_question,
    save_answer,
    complete_game,
)

router = Router()

# Временные данные активных просмотров
current_profile = {}



# =========================================================
# БАН: забаненные не пользуются ботом
# =========================================================

async def ban_middleware(handler, event, data):
    """Бан + серия дней: один запрос к базе на апдейт."""
    user = data.get("event_from_user")
    info = await touch_user(user.id, user.username or "") if user else None

    if info and info["is_banned"] and user.id != ADMIN_ID:
        if isinstance(event, CallbackQuery):
            await event.answer(ui.BANNED, show_alert=True)
        else:
            await event.answer(ui.BANNED)
        return None

    result = await handler(event, data)

    # первый заход за день: напоминаем про серию (на /start она и так видна)
    is_start = isinstance(event, Message) and (event.text or "").startswith("/start")

    if info and info["first_today"] and info["streak_days"] >= 2 and not is_start:
        try:
            await event.bot.send_message(
                user.id, ui.streak_notice(info["streak_days"])
            )
        except Exception:
            logging.exception("Не удалось отправить серию %s", user.id)

    return result


async def flood_middleware(handler, event, data):
    """Больше 25 нажатий за 10 секунд — молча игнорируем (кроме админа)."""
    user = data.get("event_from_user")
    if user and user.id != ADMIN_ID and not ratelimit.hit("flood", user.id):
        if isinstance(event, CallbackQuery):
            await event.answer(ui.TOO_FAST)
        return None
    return await handler(event, data)


router.message.outer_middleware(flood_middleware)
router.callback_query.outer_middleware(flood_middleware)
router.message.outer_middleware(ban_middleware)
router.callback_query.outer_middleware(ban_middleware)


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def same_city(first, second) -> bool:
    return bool(
        first["city"]
        and second["city"]
        and first["city"].strip().lower() == second["city"].strip().lower()
    )


def calculate_vibe(first, second):
    """
    Примерный процент вайба.
    Это не научный тест — просто оценка по общим интересам и городу.
    """

    common = get_common_interests(
        normalize_interests(first["interests"] or ""),
        normalize_interests(second["interests"] or ""),
    )

    score = 40 + min(len(common) * 10, 40)

    if same_city(first, second):
        score += 15

    return min(score, 95), common


async def send_profile(message, person, viewer_id):
    viewer = await get_user(viewer_id)
    vibe, common = calculate_vibe(viewer, person)

    current_profile[viewer_id] = person["telegram_id"]

    # Фото скрыто до взаимного лайка
    await message.answer(
        ui.search_card(person, vibe, common, same_city(viewer, person)),
        reply_markup=profile_actions(person["telegram_id"]),
    )


async def show_next_profile(message, user_id):
    """Показывает следующую подходящую анкету."""

    viewer = await get_user(user_id)

    if not viewer:
        await message.answer(ui.NEED_START)
        return

    candidates = await get_candidates(user_id)

    # Дополнительная проверка пола
    viewer_gender = viewer.get("search_gender") or "all"

    filtered = []

    for person in candidates:
        if person["telegram_id"] == user_id or not is_adult(person["age"]):
            continue

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
        await message.answer(ui.NO_CANDIDATES, reply_markup=main_menu())
        return

    # Не показываем текущую анкету повторно подряд
    previous_id = current_profile.get(user_id)
    available = [
        person for person in filtered
        if person["telegram_id"] != previous_id
    ]

    pool = available or filtered
    # Вайб-час: сначала те, кто сейчас в сети
    if vibehour.is_active():
        pool = [p for p in pool if vibehour.is_online(p)] or pool
    # Награда за друга: анкеты с бустом первыми
    pool = [p for p in pool if boost.is_boosted(p)] or pool

    await send_profile(message, random.choice(pool), user_id)


async def user_profile_message(message, user):
    """Показывает собственную анкету."""

    stats = await get_stats(user["telegram_id"])
    done, total = ui.achievements_progress(stats)
    city = await citygoal.progress(user["city"])
    text = ui.own_profile(user, stats, done, total, city)

    if user["photo_id"]:
        await message.answer_photo(
            photo=user["photo_id"],
            caption=text,
            reply_markup=main_menu(),
        )
    else:
        await message.answer(text, reply_markup=main_menu())


async def notify_liked(bot, person_id):
    """Тебя оценили: без имени, чтобы сохранить интригу."""
    try:
        await bot.send_message(
            person_id,
            ui.LIKED_YOU,
            reply_markup=liked_you_keyboard(),
        )
    except Exception:
        logging.exception("Не удалось отправить уведомление %s", person_id)


async def notify_mutual(bot, user_id, person_id):
    """Взаимный вайб: каждому открываем фото и анкету второго."""

    user = await get_user(user_id)
    person = await get_user(person_id)

    for viewer_id, other in ((user_id, person), (person_id, user)):
        if not other:
            continue

        caption = ui.mutual_caption(other)
        me_side = user if viewer_id == user_id else person
        vibe, _ = calculate_vibe(me_side, other)
        keyboard = mutual_actions(
            other["telegram_id"], other["username"],
            story=story_button(vibe, other["full_name"]),
        )

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
# АДМИН
# =========================================================

@router.message(Command("week"))
async def admin_week_handler(message: Message):
    """Админу: анонимная статистика недели для роликов."""
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(await weeklystats.build())


@router.message(Command("sources"))
async def admin_sources_handler(message: Message):
    """Админу: сколько людей пришло по каждой партнёрской метке."""
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(ui.admin_sources(await source_stats()))


@router.message(Command("emojiset"))
async def emoji_set_handler(message: Message, command: CommandObject):
    """Админу: список эмодзи набора с их id, чтобы подключить в ui.NEON."""
    if message.from_user.id != ADMIN_ID:
        return

    name = (command.args or "VibemeterNeon").strip().split("/")[-1]
    try:
        sticker_set = await message.bot.get_sticker_set(name)
    except Exception as err:
        await message.answer(f"Не получилось открыть набор {html.escape(name)}: {html.escape(str(err))}")
        return

    lines = [f"Набор {html.escape(sticker_set.title)}: {len(sticker_set.stickers)} шт.", ""]
    for i, sticker in enumerate(sticker_set.stickers, 1):
        lines.append(f"{i}. {sticker.emoji or '?'} <code>{sticker.custom_emoji_id}</code>")
    # у Telegram лимит на длину сообщения
    for start in range(0, len(lines), 40):
        await message.answer("\n".join(lines[start:start + 40]))

    # превью: сами картинки рядом с номерами, чтобы понять, какой есть какой
    preview = ["Превью (номер и картинка):", ""]
    for i, sticker in enumerate(sticker_set.stickers, 1):
        preview.append(
            f'{i}. <tg-emoji emoji-id="{sticker.custom_emoji_id}">{sticker.emoji or "?"}</tg-emoji>'
        )
    await message.answer("\n".join(preview))


# =========================================================
# СОГЛАСИЕ И ПОЛИТИКА
# =========================================================

@router.message(Command("privacy"))
async def privacy_handler(message: Message):
    await message.answer(ui.PRIVACY)


@router.callback_query(F.data == "consent:policy")
async def consent_policy_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(ui.PRIVACY)


@router.callback_query(F.data == "consent:accept")
async def consent_accept_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    # Запись создаётся только после согласия
    ref = (await state.get_data()).get("ref")
    if not await get_user(callback.from_user.id):
        await create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=callback.from_user.full_name,
        )
        if ref:
            await add_referral(callback.from_user.id, ref)

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.clear()
    await callback.message.answer(ui.PROFILE_START)
    await state.set_state(ProfileState.name)


# =========================================================
# START
# =========================================================

async def send_vibe_test(message: Message, code: str):
    if code:
        test = await get_vibe_test(code)
        if test:
            text, page = ui.vt_invite(test["owner_name"] or "друга"), f"vt?c={code}"
        else:
            text, page = ui.VT_NOT_FOUND, "vt"
    else:
        text, page = ui.VT_START, "vt"

    keyboard = open_app_keyboard(page)
    if not keyboard:
        await message.answer(ui.VT_NO_APP)
        return
    await message.answer(text, reply_markup=keyboard)


async def send_crush(message: Message):
    keyboard = open_app_keyboard("crush")
    if not keyboard:
        await message.answer(ui.VT_NO_APP)
        return
    await message.answer(ui.CRUSH_START, reply_markup=keyboard)


@router.message(Command("crush"))
async def crush_command(message: Message):
    user = await get_user(message.from_user.id)
    if not user or user["age"] is None:
        await message.answer(ui.NEED_PROFILE)
        return
    await send_crush(message)


@router.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext,
    command: CommandObject,
):
    user = await get_user(message.from_user.id)

    # «Проверь вайб с другом»: t.me/бот?start=vt или vt_<код>, анкета не нужна
    arg = command.args or ""
    # партнёрская ссылка: t.me/бот?start=vtp_<метка> — тот же тест + учёт источника
    if re.fullmatch(r"vtp_[a-z0-9_]{1,30}", arg):
        await add_start_source(arg[4:], message.from_user.id)
        arg = "vt"
    if arg == "vt" or arg.startswith("vt_"):
        await send_vibe_test(message, arg[3:])
        return

    if not user:
        await state.clear()
        # Ссылка друга: t.me/бот?start=ref_<id>, запоминаем до согласия
        arg = command.args or ""
        if arg.startswith("ref_") and arg[4:].isdigit():
            await state.update_data(ref=int(arg[4:]))
        await message.answer(ui.CONSENT, reply_markup=consent_keyboard())
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

        # «Кто-то хочет узнать ваш вайб»: t.me/бот?start=sc
        if command.args == "sc":
            await message.answer(ui.MAIN_MENU, reply_markup=main_menu())
            await send_crush(message)
            return

        # Ссылка из Mini App: t.me/бот?start=game
        if command.args == "game":
            await message.answer(ui.MAIN_MENU, reply_markup=main_menu())
            await find_game(message, message.from_user.id)
            return

        await message.answer(
            ui.welcome_back(user["streak_days"]),
            reply_markup=main_menu(),
        )
        app_keyboard = open_app_keyboard()
        if app_keyboard:
            await message.answer(ui.OPEN_APP_HINT, reply_markup=app_keyboard)
        return

    current_state = await state.get_state()

    if current_state and current_state.startswith("ProfileState:"):
        await message.answer(ui.PROFILE_CONTINUE)
        return

    await state.clear()
    await message.answer(ui.PROFILE_RESTART)
    await state.set_state(ProfileState.name)


# =========================================================
# СОЗДАНИЕ АНКЕТЫ
# =========================================================

@router.message(F.text.in_(ui.CANCEL_ALIASES))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(ui.CANCELLED, reply_markup=main_menu())


@router.message(ProfileState.name, F.text)
async def profile_name(message: Message, state: FSMContext):
    name = message.text.strip()

    if not valid_name(name):
        await message.answer(ui.ERR_NAME)
        return

    await state.update_data(name=name)
    await message.answer(ui.ASK_AGE)
    await state.set_state(ProfileState.age)


@router.message(ProfileState.age, F.text)
async def profile_age(message: Message, state: FSMContext):
    age_digits = "".join(
        char for char in message.text
        if char.isdigit()
    )

    if not age_digits:
        await message.answer(ui.ERR_AGE_FORMAT)
        return

    age = int(age_digits)

    if age < MIN_AGE:
        # Анкету младше 18 не сохраняем
        await state.clear()
        await delete_user(message.from_user.id)
        await message.answer(ui.UNDER_18, reply_markup=ReplyKeyboardRemove())
        return

    if age > MAX_AGE:
        await message.answer(ui.err_age_max(MAX_AGE))
        return

    await state.update_data(age=age)
    await message.answer(ui.ASK_GENDER, reply_markup=gender_keyboard())


@router.callback_query(F.data.startswith("gender:"))
async def profile_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split(":")[1]

    if gender not in ("male", "female"):
        await callback.answer()
        return

    await state.update_data(gender=gender)
    await callback.message.edit_text(ui.ASK_CITY)
    await state.set_state(ProfileState.city)
    await callback.answer()


@router.message(ProfileState.city, F.text)
async def profile_city(message: Message, state: FSMContext):
    city = message.text.strip()

    if not valid_city(city):
        await message.answer(ui.ERR_CITY)
        return

    await state.update_data(city=city)
    await message.answer(ui.ASK_INTERESTS)
    await state.set_state(ProfileState.interests)


@router.message(ProfileState.interests, F.text)
async def profile_interests(message: Message, state: FSMContext):
    interests = normalize_interests(message.text)

    if not interests:
        await message.answer(ui.ERR_INTERESTS)
        return

    await state.update_data(interests=interests)
    await message.answer(ui.ASK_ABOUT)
    await state.set_state(ProfileState.description)


@router.message(ProfileState.description, F.text)
async def profile_description(message: Message, state: FSMContext):
    description = message.text.strip()

    if not valid_description(description):
        await message.answer(ui.ERR_ABOUT)
        return

    await state.update_data(description=description)
    await message.answer(ui.ASK_PHOTO)
    await state.set_state(ProfileState.photo)


@router.message(ProfileState.photo, F.photo)
async def profile_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    gender = data.get("gender")

    if not gender:
        await message.answer(ui.ERR_GENDER_LOST, reply_markup=gender_keyboard())
        return

    before = await get_user(message.from_user.id)
    is_new = not before or not before["photo_id"]

    await update_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data["name"],
        age=data["age"],
        city=data["city"],
        interests=data["interests"],
        description=data["description"],
        photo_id=message.photo[-1].file_id,
        gender=gender,
    )

    await message.answer(ui.ASK_SEARCH, reply_markup=search_gender_keyboard())
    await admin.review_photo(message.bot, message.from_user.id, is_new)


@router.callback_query(F.data.startswith("search_gender:"))
async def profile_search_gender(
    callback: CallbackQuery,
    state: FSMContext,
):
    search_gender = callback.data.split(":")[1]

    if search_gender not in ("male", "female", "all"):
        await callback.answer()
        return

    await update_user(
        telegram_id=callback.from_user.id,
        search_gender=search_gender,
    )

    # шаг анкеты или смена в настройках
    creating = await state.get_state() == ProfileState.photo.state
    await state.clear()

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        ui.PROFILE_DONE if creating else ui.SEARCH_SAVED,
        reply_markup=main_menu(),
    )

    if creating:
        inviter = await get_inviter(callback.from_user.id)
        if inviter:
            try:
                total = await count_referrals(inviter)
                await boost.reward_inviter(inviter)
                inviter_user = await get_user(inviter)
                city = await citygoal.progress(inviter_user["city"] if inviter_user else None)
                await callback.bot.send_message(
                    inviter, ui.friend_joined(total, city),
                )
            except Exception:
                logging.exception("referral notify failed")


@router.message(StateFilter(
    ProfileState.name, ProfileState.age, ProfileState.city,
    ProfileState.interests, ProfileState.description,
))
async def profile_text_invalid(message: Message):
    await message.answer(ui.ERR_TEXT_ONLY)


@router.message(ProfileState.photo)
async def profile_photo_invalid(message: Message):
    await message.answer(ui.ERR_PHOTO_ONLY)


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

@router.message(F.text.in_(ui.menu_texts(ui.MENU_FIND)))
async def find_vibe_handler(message: Message):
    await show_next_profile(message, message.from_user.id)


@router.message(F.text.in_(ui.menu_texts(ui.MENU_LIKES)))
async def my_vibes_handler(message: Message):
    await show_incoming_likes(message, message.from_user.id)


@router.callback_query(F.data == "my_vibes")
async def my_vibes_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await show_incoming_likes(callback.message, callback.from_user.id)


@router.callback_query(F.data == "dismiss")
async def dismiss_callback(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        await callback.message.edit_reply_markup(reply_markup=None)


async def show_incoming_likes(message, user_id):
    likes = await get_incoming_likes(user_id)

    if not likes:
        await message.answer(ui.NO_LIKES, reply_markup=main_menu())
        return

    viewer = await get_user(user_id)

    await message.answer(ui.likes_header(len(likes)))

    for person in likes[:10]:
        vibe, common = calculate_vibe(viewer, person) if viewer else (None, None)

        await message.answer(
            ui.profile_card(
                person,
                vibe=vibe,
                common=common,
                same_city=bool(viewer) and same_city(viewer, person),
            ),
            reply_markup=incoming_actions(person["telegram_id"]),
        )


@router.message(F.text.in_(ui.menu_texts(ui.MENU_PROFILE)))
async def my_profile_handler(message: Message):
    user = await get_user(message.from_user.id)

    if not user:
        await message.answer(ui.NEED_START)
        return

    await user_profile_message(message, user)


@router.callback_query(F.data == "vh_off")
async def vibe_hour_off(callback: CallbackQuery):
    await set_vibe_hour_notify(callback.from_user.id, False)
    await callback.answer()
    await callback.message.answer(ui.VH_OFF, reply_markup=vibe_hour_on_keyboard())


@router.callback_query(F.data == "vh_on")
async def vibe_hour_on(callback: CallbackQuery):
    await set_vibe_hour_notify(callback.from_user.id, True)
    await callback.answer()
    await callback.message.edit_text(ui.VH_ON)


@router.callback_query(F.data == "browse")
async def browse_callback(callback: CallbackQuery):
    await callback.answer()
    await show_next_profile(callback.message, callback.from_user.id)


# =========================================================
# ВОПРОСЫ
# =========================================================

@router.callback_query(F.data.startswith("question:"))
async def question_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    person_id = int(callback.data.split(":")[1])

    if person_id == callback.from_user.id:
        await callback.answer(ui.QUESTION_SELF, show_alert=True)
        return

    if not await get_user(person_id):
        await callback.answer(ui.USER_NOT_FOUND, show_alert=True)
        return

    await state.clear()
    await state.update_data(question_to=person_id)
    await state.set_state(QuestionState.answering)

    await callback.answer()
    await callback.message.answer(ui.ASK_QUESTION, reply_markup=cancel_keyboard())


@router.message(QuestionState.answering, F.text)
async def question_text_handler(
    message: Message,
    state: FSMContext,
):
    question_text = (message.text or "").strip()

    if question_text.startswith("/"):
        await message.answer(ui.QUESTION_NO_COMMANDS)
        return

    if not question_text or len(question_text) > 500:
        await message.answer(ui.QUESTION_BAD_LEN)
        return

    if message.from_user.id != ADMIN_ID and not ratelimit.hit("question", message.from_user.id):
        await state.clear()
        await message.answer(ui.TOO_FAST_QUESTIONS, reply_markup=main_menu())
        return

    data = await state.get_data()
    person_id = data.get("question_to")

    if not person_id:
        await state.clear()
        await message.answer(ui.QUESTION_NO_TARGET, reply_markup=main_menu())
        return

    question_id = await send_question(
        bot=message.bot,
        from_user=message.from_user.id,
        to_user=person_id,
        text=question_text,
    )

    await state.clear()

    await message.answer(
        ui.QUESTION_SENT if question_id is not None else ui.QUESTION_FAILED,
        reply_markup=main_menu(),
    )


@router.callback_query(F.data.startswith("answer_q:"))
async def answer_question_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    question_id = int(callback.data.split(":")[1])
    question = await get_question_data(question_id)

    if not question or question["to_user"] != callback.from_user.id:
        await callback.answer(ui.QUESTION_NOT_FOUND, show_alert=True)
        return

    if question["answered"]:
        await callback.answer(ui.QUESTION_ALREADY, show_alert=True)
        return

    await state.clear()
    await state.update_data(question_id=question_id)
    await state.set_state(QuestionState.replying)

    await callback.answer()
    await callback.message.answer(ui.ASK_REPLY, reply_markup=cancel_keyboard())


@router.message(QuestionState.replying, F.text)
async def question_reply_handler(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()
    question_id = data.get("question_id")

    success = question_id and await submit_answer(
        message.bot,
        question_id,
        message.text,
        message.from_user.id,
    )

    await state.clear()

    await message.answer(
        ui.REPLY_SENT if success else ui.REPLY_FAILED,
        reply_markup=main_menu(),
    )


# =========================================================
# ЛАЙК / ПРОПУСК
# =========================================================

@router.callback_query(F.data.startswith("like:"))
async def like_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    if user_id != ADMIN_ID and not ratelimit.hit("like", user_id):
        await callback.answer(ui.TOO_FAST_LIKES, show_alert=True)
        return

    if person_id == user_id:
        await callback.answer(ui.TOAST_SELF, show_alert=True)
        return

    is_new = await add_like(from_user=user_id, to_user=person_id)
    mutual = await has_like(from_user=person_id, to_user=user_id)

    await callback.answer(ui.TOAST_MUTUAL if mutual else ui.TOAST_LIKE)
    await callback.message.edit_reply_markup(reply_markup=None)

    if mutual:
        await notify_mutual(callback.bot, user_id, person_id)
        return

    if is_new:
        await notify_liked(callback.bot, person_id)

    await show_next_profile(callback.message, user_id)


@router.callback_query(F.data.startswith("skip:"))
async def skip_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])

    await add_skip(from_user=callback.from_user.id, to_user=person_id)

    await callback.answer(ui.TOAST_SKIP)
    await callback.message.edit_reply_markup(reply_markup=None)
    await show_next_profile(callback.message, callback.from_user.id)


@router.callback_query(F.data.startswith("incoming_like:"))
async def incoming_like_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    if user_id != ADMIN_ID and not ratelimit.hit("like", user_id):
        await callback.answer(ui.TOO_FAST_LIKES, show_alert=True)
        return

    await add_like(from_user=user_id, to_user=person_id)
    mutual = await has_like(from_user=person_id, to_user=user_id)

    await callback.answer(ui.TOAST_MUTUAL if mutual else ui.TOAST_LIKE)
    await callback.message.edit_reply_markup(reply_markup=None)

    if mutual:
        await notify_mutual(callback.bot, user_id, person_id)


@router.callback_query(F.data.startswith("incoming_skip:"))
async def incoming_skip_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])

    await add_skip(from_user=callback.from_user.id, to_user=person_id)

    await callback.answer(ui.TOAST_SKIP)
    await callback.message.edit_reply_markup(reply_markup=None)


@router.callback_query(F.data.startswith("contact:"))
async def contact_callback(callback: CallbackQuery):
    """Запасной путь «Написать», когда у человека нет username."""

    person_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    person = await get_user(person_id)

    if not person:
        await callback.answer(ui.USER_NOT_FOUND, show_alert=True)
        return

    # Контакт открывается только при взаимном вайбе
    mutual = (
        await has_like(from_user=user_id, to_user=person_id)
        and await has_like(from_user=person_id, to_user=user_id)
    )

    if not mutual:
        await callback.answer(ui.CONTACT_LOCKED, show_alert=True)
        return

    await callback.answer()

    username = (person["username"] or "").lstrip("@")

    if username:
        await callback.message.answer(
            ui.contact_text(username),
            reply_markup=contact_keyboard(username),
        )
    else:
        await callback.message.answer(ui.mutual_no_username(person))


# =========================================================
# ЖАЛОБЫ И БЛОК
# =========================================================

@router.callback_query(F.data.startswith("report:"))
async def report_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])

    await callback.answer()

    if person_id == callback.from_user.id:
        return

    await callback.message.answer(
        ui.REPORT_ASK,
        reply_markup=report_reasons_keyboard(person_id),
    )


@router.callback_query(F.data.startswith("report_reason:"))
async def report_reason_callback(callback: CallbackQuery):
    _, person_id, code = callback.data.split(":")
    person_id = int(person_id)
    reason = ui.REPORT_REASONS.get(code, "Другое")
    user_id = callback.from_user.id

    if person_id == user_id:
        await callback.answer()
        return

    is_new = await add_report(user_id, person_id, reason)

    await callback.answer(ui.TOAST_REPORT)
    await callback.message.edit_text(ui.REPORT_SENT)

    if is_new:
        await notify_admin_report(callback.bot, user_id, person_id, reason)

    await show_next_profile(callback.message, user_id)


@router.callback_query(F.data.startswith("block:"))
async def block_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])

    await add_block(from_user=callback.from_user.id, to_user=person_id)

    await callback.answer(ui.TOAST_HIDDEN)
    await callback.message.edit_reply_markup(reply_markup=None)
    await show_next_profile(callback.message, callback.from_user.id)


async def notify_admin_report(bot, from_user, person_id, reason):
    """Жалоба приходит админу карточкой: фото, цифры, бан в одну кнопку."""
    person = await get_user(person_id)
    if not person:
        return
    note = (
        f"🚩 <b>Новая жалоба</b>: {html.escape(reason)}\n"
        f"От <code>{from_user}</code> · /u_{from_user}"
    )
    try:
        await admin.send_card(bot, person, note=note, report=True)
    except Exception:
        logging.exception("Не удалось отправить жалобу админу")


async def apply_ban(bot, person_id, banned):
    found = await set_banned(person_id, banned)

    if found and banned:
        try:
            await bot.send_message(person_id, ui.BANNED)
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

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        ui.admin_banned(person_id) if found else ui.ADMIN_USER_GONE
    )


@router.callback_query(F.data.startswith("admin_dismiss:"))
async def admin_dismiss_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer()
        return

    await dismiss_reports(int(callback.data.split(":")[1]))

    await callback.answer(ui.ADMIN_DISMISSED)
    await callback.message.edit_reply_markup(reply_markup=None)


@router.message(Command("ban", "unban"))
async def admin_ban_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = (message.text or "").split()
    banned = parts[0].lstrip("/").split("@")[0] == "ban"

    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer(ui.ADMIN_BAN_FORMAT)
        return

    person_id = int(parts[1])

    if not await apply_ban(message.bot, person_id, banned):
        await message.answer(ui.ADMIN_USER_GONE)
        return

    await message.answer(
        ui.admin_banned(person_id) if banned else ui.admin_unbanned(person_id)
    )


# =========================================================
# СТАТИСТИКА
# =========================================================

@router.message(F.text.in_(ui.menu_texts(ui.MENU_STATS)))
async def statistics_handler(message: Message):
    if not await get_user(message.from_user.id):
        await message.answer(ui.NEED_START)
        return

    await message.answer(ui.stats_full(await get_stats(message.from_user.id)))


@router.callback_query(F.data == "achievements")
async def achievements_callback(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        ui.hall_of_fame(await get_stats(callback.from_user.id))
    )


# =========================================================
# НАСТРОЙКИ
# =========================================================

@router.message(F.text.in_(ui.menu_texts(ui.MENU_SETTINGS)))
async def settings_handler(message: Message):
    await message.answer(ui.SETTINGS, reply_markup=settings_keyboard())


@router.callback_query(F.data == "edit_profile")
async def edit_profile_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    await callback.answer()
    await state.clear()
    await callback.message.answer(ui.EDIT_START, reply_markup=cancel_keyboard())
    await state.set_state(ProfileState.name)


@router.callback_query(F.data == "search_settings")
async def search_settings_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        ui.SEARCH_CHOOSE,
        reply_markup=search_gender_keyboard(),
    )


@router.callback_query(F.data == "blocked_users")
async def blocked_users_callback(callback: CallbackQuery):
    await callback.answer()

    blocked = await get_blocked_users(callback.from_user.id)

    await callback.message.answer(
        ui.blocked_list(blocked) if blocked else ui.BLOCKED_EMPTY
    )


@router.callback_query(F.data == "delete_profile")
async def delete_profile_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        ui.DELETE_ASK,
        reply_markup=delete_confirm_keyboard(),
    )


@router.callback_query(F.data == "delete_confirm")
async def delete_confirm_callback(
    callback: CallbackQuery,
    state: FSMContext,
):
    user_id = callback.from_user.id

    try:
        await delete_user(user_id)
    except Exception:
        logging.exception("Не удалось удалить профиль %s", user_id)
        await callback.answer(ui.DELETE_FAILED, show_alert=True)
        return

    await state.clear()
    current_profile.pop(user_id, None)
    game_queue.pop(user_id, None)

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(ui.DELETED, reply_markup=ReplyKeyboardRemove())


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(ui.MAIN_MENU, reply_markup=main_menu())


# =========================================================
# ВАЙБ-ИГРЫ
# =========================================================

@router.message(F.text.in_(ui.menu_texts(ui.MENU_GAMES)))
async def vibe_games_handler(message: Message):
    await find_game(message, message.from_user.id)


@router.callback_query(F.data == "play_again")
async def play_again_callback(callback: CallbackQuery):
    await callback.answer()
    await find_game(callback.message, callback.from_user.id)


async def find_game(message: Message, user_id: int):
    """Ставит в очередь или сразу находит соперника.
    user_id передаём явно: из кнопки message — это сообщение бота."""
    user = await get_user(user_id)

    if not user or not is_adult(user["age"]):
        await message.answer(ui.GAME_NEED_PROFILE)
        return

    # Убираем пользователя из старой очереди
    game_queue.pop(user_id, None)

    # чистим протухшие записи
    now = time.time()
    for uid in [u for u, (t, _) in game_queue.items() if now - t > 15 * 60]:
        game_queue.pop(uid, None)

    opponent_id = None

    for candidate_id in list(game_queue):
        candidate = await get_user(candidate_id)

        if (
            candidate and not candidate["is_banned"]
            and is_adult(candidate["age"])
            and not await is_blocked(user_id, candidate_id)
            and not await is_blocked(candidate_id, user_id)
        ):
            opponent_id = candidate_id
            break

        game_queue.pop(candidate_id, None)

    if opponent_id is None:
        game_queue[user_id] = (now, "bot")
        await message.answer(ui.GAME_WAITING, reply_markup=main_menu())
        return

    _, opponent_channel = game_queue.pop(opponent_id)

    game = await start_game(opponent_id, user_id)

    # Первый вопрос сразу — без лишней кнопки «Начать»
    await send_game_question(
        message.bot, user_id, game["id"], intro=ui.GAME_FOUND
    )

    if opponent_channel == "bot":
        await send_game_question(
            message.bot, opponent_id, game["id"], intro=ui.GAME_FOUND
        )
    else:
        # соперник ждал в приложении: зовём его обратно
        try:
            await message.bot.send_message(
                opponent_id,
                ui.GAME_FOUND_PING,
                reply_markup=open_app_keyboard("games"),
            )
        except Exception:
            logging.info("Не удалось позвать соперника %s", opponent_id)


async def send_game_question(bot, chat_id, game_id, intro=None):
    """Шлёт игроку его текущий вопрос. False — вопросов не осталось."""
    question = await get_current_question(game_id, chat_id)

    if not question:
        return False

    try:
        if intro:
            await bot.send_message(chat_id, intro)

        await bot.send_message(
            chat_id,
            ui.game_question(question["index"], question["question"]),
            reply_markup=game_keyboard(
                game_id,
                question["index"],
                question["a"],
                question["b"],
            ),
        )
    except Exception:
        logging.exception("Не удалось отправить вопрос игры %s", chat_id)

    return True


@router.callback_query(F.data.startswith("game_start:"))
async def game_start_callback(callback: CallbackQuery):
    game_id = int(callback.data.split(":")[1])

    if not await get_current_question(game_id, callback.from_user.id):
        await callback.answer(ui.GAME_NOT_FOUND, show_alert=True)
        return

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await send_game_question(callback.bot, callback.from_user.id, game_id)


@router.callback_query(F.data.startswith("game_answer:"))
async def game_answer_callback(callback: CallbackQuery):
    _, game_id, question_index, answer = callback.data.split(":")
    game_id = int(game_id)
    user_id = callback.from_user.id

    if not await save_answer(game_id, user_id, int(question_index), answer):
        await callback.answer(ui.GAME_ANSWER_REJECTED, show_alert=True)
        return

    await callback.answer(ui.TOAST_ANSWER)
    await callback.message.edit_reply_markup(reply_markup=None)

    if await send_game_question(callback.bot, user_id, game_id):
        return

    result = await complete_game(game_id)
    if not result:
        # игру могли закрыть из приложения за долю секунды до нас
        finished = await get_game(game_id)
        if finished and finished["status"] == "finished":
            result = await calculate_result(game_id)

    if not result:
        await callback.message.answer(ui.GAME_WAIT_OTHER)

        # напоминаем сопернику, что ждут его
        game = await get_game(game_id)
        opponent_id = (
            game["user_two"] if game["user_one"] == user_id
            else game["user_one"]
        )
        await send_game_question(
            callback.bot, opponent_id, game_id, intro=ui.GAME_YOUR_TURN
        )
        return

    text = ui.game_result(result["matches"], result["percentage"])

    opponent_id = (
        result["user_two"]
        if result["user_one"] == user_id
        else result["user_one"]
    )

    me = await get_user(user_id)
    opponent = await get_user(opponent_id)
    story = lambda other: story_button(
        result["percentage"], other["full_name"] if other else "",
        result["matches"], result["total"],
    )

    await callback.message.answer(
        text,
        reply_markup=game_result_actions(opponent_id, story(opponent)),
    )

    try:
        await callback.bot.send_message(
            opponent_id,
            text,
            reply_markup=game_result_actions(user_id, story(me)),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("game_like:"))
async def game_like_callback(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    if user_id != ADMIN_ID and not ratelimit.hit("like", user_id):
        await callback.answer(ui.TOO_FAST_LIKES, show_alert=True)
        return

    if person_id == user_id:
        await callback.answer(ui.TOAST_SELF, show_alert=True)
        return

    is_new = await add_like(from_user=user_id, to_user=person_id)
    mutual = await has_like(from_user=person_id, to_user=user_id)

    await callback.answer(ui.TOAST_MUTUAL if mutual else ui.TOAST_LIKE)
    await callback.message.edit_reply_markup(reply_markup=None)

    if mutual:
        await notify_mutual(callback.bot, user_id, person_id)
    elif is_new:
        await notify_liked(callback.bot, person_id)


# =========================================================
# ПРОЧИЙ ТЕКСТ
# =========================================================

@router.message(F.text)
async def universal_text_handler(
    message: Message,
    state: FSMContext,
):
    # Сюда попадает текст, который не поймал ни один хендлер.
    # Ответы на вопросы — только через кнопку «Ответить».
    if await state.get_state() is not None:
        return

    if not await get_user(message.from_user.id):
        await message.answer(ui.NEED_START)
        return

    await message.answer(ui.UNKNOWN, reply_markup=main_menu())
