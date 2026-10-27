"""Админка: /admin — всё на одном экране и в пару нажатий.

Главный экран с цифрами, жалобы, новые анкеты, забаненные, поиск
человека по ID или @username, карточка человека с баном в одну кнопку,
проверка каждого нового фото. Обычные эмодзи, без неона: админке нужна
надёжность, а не красота.
"""

import html
import logging
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import broadcast
import moderation
import strikes
import weeklystats
from vibehour import MSK
from config import ADMIN_ID
from database import (
    admin_counts,
    active_profiles,
    banned_users,
    broadcast_stats,
    broadcast_targets,
    count_reports,
    dismiss_reports,
    find_user_by_username,
    get_admin_stats,
    get_stats,
    get_user,
    growth_metrics,
    hide_profile_text,
    open_reports,
    recent_profiles,
    set_banned,
    vote_stats,
    warn_photo,
    source_stats,
)
from states import AdminState
import ui

router = Router()
router.message.filter(F.from_user.id == ADMIN_ID)
router.callback_query.filter(F.from_user.id == ADMIN_ID)

LIST_LIMIT = 15


def _b(text, data, style=None):
    extra = {"style": style} if style else {}
    return InlineKeyboardButton(text=text, callback_data=data, **extra)


def _kb(*rows):
    return InlineKeyboardMarkup(inline_keyboard=[list(r) for r in rows])


BACK = _b("← Админка", "adm:home")


# =========================================================
# ГЛАВНЫЙ ЭКРАН
# =========================================================

async def home_text() -> str:
    s = await get_admin_stats()
    c = await admin_counts()
    return (
        "🛠 <b>Вайбометр · админка</b>\n\n"
        f"👥 Пользователей: <b>{s['total_users']}</b> (+{s['today']} сегодня)\n"
        f"📝 Анкет: <b>{s['profiles']}</b> · с фото {s['photos']}\n"
        f"🟢 Сейчас в сети: <b>{c['online']}</b> · заходили сегодня: {c['active_today']}\n\n"
        f"💜 Вайбов: {s['likes']} · взаимных: <b>{s['mutual']}</b>\n"
        f"🎮 Игр: {s['games']} · ❓ вопросов: {s['questions']}\n\n"
        f"🚩 Открытых жалоб: <b>{c['open_reports']}</b> · 🚫 в бане: {c['banned']}\n\n"
        f"{growth_text(await growth_metrics())}\n\n"
        f"<i>Обновлено {datetime.now(MSK).strftime('%H:%M')} МСК</i>"
    )


def _pct(part, whole) -> str:
    return f"{round(part * 100 / whole)}%" if whole else "—"


# бесплатный Neon: 0.5 ГБ на проект, дальше база останавливается
DB_LIMIT_MB = 512


def growth_text(g) -> str:
    gendered = g["male"] + g["female"]
    if g["d1_base"]:
        d1 = f"<b>{_pct(g['d1_back'], g['d1_base'])}</b> ({g['d1_back']} из {g['d1_base']})"
    else:
        d1 = "первые цифры послезавтра (ждём, пока пройдёт следующий день)"
    db_mb = g["db_bytes"] / 1024 / 1024
    db_warn = " ⚠️" if db_mb > DB_LIMIT_MB * 0.7 else ""
    return (
        "📐 <b>Метрики</b>\n"
        f"👩 Девушек {_pct(g['female'], gendered)} · 👨 парней {_pct(g['male'], gendered)} "
        f"({g['female']} / {g['male']})\n"
        f"🔁 Вернулись на след. день (D1): {d1}, "
        f"считаем с {g['d1_since']:%d.%m}\n"
        f"🔁 Вчерашние новички сегодня: {g['y_back']} из {g['y_new']} · "
        f"хоть раз возвращались: {_pct(g['ever_back'], g['total_users'])}\n"
        f"💞 Есть взаимный вайб: <b>{g['with_mutual']}</b> из {g['profiles']} анкет "
        f"({_pct(g['with_mutual'], g['profiles'])})\n"
        f"✍️ Нажали «Написать»: <b>{g['writers']}</b> чел. · {g['write_clicks']} раз "
        f"(Mini App и бот без @username)\n"        f"📇 С @username: <b>{_pct(g['with_username'], g['profiles'])}</b> анкет "
        f"({g['with_username']} из {g['profiles']}) — остальным «Написать» может не открыться\n"
        f"🗄 База: {db_mb:.0f} МБ из {DB_LIMIT_MB}{db_warn}"
    )


async def home_keyboard():
    c = await admin_counts()
    reports = f"🚩 Жалобы ({c['open_reports']})" if c["open_reports"] else "🚩 Жалобы"
    return _kb(
        [_b("🔄 Обновить", "adm:home"), _b(reports, "adm:reports", "danger" if c["open_reports"] else None)],
        [_b("🆕 Новые анкеты", "adm:new"), _b("🚫 Забаненные", "adm:banned")],
        [_b("🔎 Найти человека", "adm:find", "primary")],
        [_b("📊 Неделя", "adm:week"), _b("📈 Источники", "adm:sources")],
        [_b("📣 Рассылка и голоса", "adm:bc")],
        [_b("🙏 «Мы снова в строю» всем", "adm:sorry")],
        [_b("🧹 Проверить анкеты на мат", "adm:scan")],
    )


@router.message(Command("admin"))
async def admin_home(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(await home_text(), reply_markup=await home_keyboard())


async def _show(callback: CallbackQuery, text: str, keyboard):
    """Меняем текущее сообщение; если это фото — шлём новое."""
    await callback.answer()
    try:
        if callback.message.photo:
            raise ValueError
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "adm:home")
async def cb_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _show(callback, await home_text(), await home_keyboard())


# =========================================================
# СПИСКИ
# =========================================================

def _line(p) -> str:
    age = f", {p['age']}" if p.get("age") else ""
    city = f" · {html.escape(p['city'])}" if p.get("city") else ""
    ban = " 🚫" if p.get("is_banned") else ""
    return f"{html.escape(p['full_name'] or '—')}{age}{city}{ban} — /u_{p['telegram_id']}"


@router.callback_query(F.data == "adm:new")
async def cb_new(callback: CallbackQuery):
    rows = await recent_profiles(LIST_LIMIT)
    lines = ["🆕 <b>Новые анкеты</b>", ""]
    for p in rows:
        lines.append(f"{p['created_at'].strftime('%d.%m %H:%M')} · {_line(p)}")
    if not rows:
        lines.append("Пока пусто")
    lines += ["", "<i>Нажми /u_… — откроется карточка с фото и баном</i>"]
    await _show(callback, "\n".join(lines), _kb([BACK]))


@router.callback_query(F.data == "adm:banned")
async def cb_banned(callback: CallbackQuery):
    rows = await banned_users(LIST_LIMIT)
    lines = ["🚫 <b>Забаненные</b>", ""] + [_line(p) for p in rows]
    if not rows:
        lines.append("Никого")
    await _show(callback, "\n".join(lines), _kb([BACK]))


@router.callback_query(F.data == "adm:reports")
async def cb_reports(callback: CallbackQuery):
    rows = await open_reports(5)
    if not rows:
        await _show(callback, "🚩 <b>Жалобы</b>\n\nОткрытых жалоб нет", _kb([BACK]))
        return
    await callback.answer()
    for r in rows:
        person = await get_user(r["to_user"])
        if person:
            note = f"🚩 Жалоб: {r['n']} · последняя: {html.escape(r['last_reason'] or '—')}"
            await send_card(callback.bot, person, note=note, report=True)
    await callback.message.answer(f"Показал {len(rows)}. Остальные — после разбора", reply_markup=_kb([BACK]))


@router.callback_query(F.data == "adm:week")
async def cb_week(callback: CallbackQuery):
    await _show(callback, await weeklystats.build(), _kb([BACK]))


@router.callback_query(F.data == "adm:sources")
async def cb_sources(callback: CallbackQuery):
    await _show(callback, ui.admin_sources(await source_stats()), _kb([BACK]))


# =========================================================
# КАРТОЧКА ЧЕЛОВЕКА
# =========================================================

def _ago(dt) -> str:
    if not dt:
        return "давно"
    minutes = int((datetime.now(timezone.utc) - dt).total_seconds() // 60)
    if minutes < 2:
        return "только что"
    if minutes < 60:
        return f"{minutes} мин назад"
    if minutes < 48 * 60:
        return f"{minutes // 60} ч назад"
    return f"{minutes // 1440} дн назад"


async def card_text(person, note: str = "") -> str:
    st = await get_stats(person["telegram_id"])
    reports = await count_reports(person["telegram_id"])
    username = f" · @{html.escape(person['username'])}" if person.get("username") else ""
    status = "🚫 <b>в бане</b>" if person["is_banned"] else "✅ активен"
    head = f"<b>{html.escape(person['full_name'] or '—')}</b>"
    if person.get("age"):
        head += f", {person['age']}"
    if person.get("city"):
        head += f" · {html.escape(person['city'])}"
    about = html.escape((person.get("description") or "")[:200])
    lines = [
        head,
        f"ID <code>{person['telegram_id']}</code>{username}",
        f"Анкета с {person['created_at'].strftime('%d.%m.%Y') if person.get('created_at') else '—'} · был(а) {_ago(person.get('last_seen'))}",
        "",
        f"💜 Получил(а) вайбов: {st['likes_received']} · отправил(а): {st['likes_sent']} · взаимных: {st['mutual_likes']}",
        f"🚩 Жалоб всего: {reports} · {status}",
    ]
    total = _strikes(person)
    if total:
        lines.append(
            f"⚠️ Предупреждений: {total} из {strikes.MAX_WARNINGS} "
            f"(фото {person.get('photo_warnings') or 0} · мат {person.get('question_strikes') or 0} · "
            f"анкета {person.get('profile_strikes') or 0})"
            + (" — следующее нарушение = бан" if total >= strikes.MAX_WARNINGS else "")
        )
    if person.get("age") and not person.get("photo_id") and not person["is_banned"]:
        lines.append("🤳 Фото нет — анкета скрыта, ждём новое")
    if person.get("age") and not person.get("description") and not person["is_banned"]:
        lines.append("📝 Анкета скрыта — ждём, пока заполнит заново")
    if about:
        lines += ["", f"<i>{about}</i>"]
    if note:
        lines = [note, ""] + lines
    return "\n".join(lines)


def _strikes(person) -> int:
    return sum(person.get(k) or 0 for k in ("photo_warnings", "question_strikes", "profile_strikes"))


def card_keyboard(person, report=False, review=False):
    pid = person["telegram_id"]
    first = (
        _b("✅ Разбанить", f"adm:unban:{pid}", "success") if person["is_banned"]
        else _b("🚫 Забанить", f"adm:ban:{pid}", "danger")
    )
    rows = [[first]]
    if not person["is_banned"]:
        last = _strikes(person) >= strikes.MAX_WARNINGS  # следующее нарушение — бан
        mark = "🚫" if last else "⚠️"
        if person.get("photo_id"):
            rows.append([_b(f"{mark} Нет лица / чужое", f"adm:warn:{pid}", "danger" if last else None)])
        if person.get("description"):
            rows.append([_b(f"{mark} Неадекватная анкета", f"adm:badprof:{pid}", "danger" if last else None)])
    if report and not person["is_banned"]:
        rows[0].append(_b("👌 Жалобы ложные", f"adm:dismiss:{pid}"))
    if review and not person["is_banned"]:
        rows[0].append(_b("✅ Фото ок", f"adm:ok:{pid}"))
    rows.append([BACK])
    return _kb(*rows)


async def send_card(bot, person, note: str = "", report=False, review=False):
    text = await card_text(person, note)
    keyboard = card_keyboard(person, report=report, review=review)
    if person.get("photo_id") and len(text) <= 1024:
        await bot.send_photo(ADMIN_ID, person["photo_id"], caption=text, reply_markup=keyboard)
    else:
        await bot.send_message(ADMIN_ID, text, reply_markup=keyboard)


@router.message(F.text.regexp(r"^/u_(\d+)"))
async def open_card(message: Message):
    person = await get_user(int(message.text.split("_", 1)[1].split("@")[0]))
    if not person:
        await message.answer("Такого пользователя нет", reply_markup=_kb([BACK]))
        return
    await send_card(message.bot, person)


@router.callback_query(F.data == "adm:find")
async def cb_find(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.find)
    await _show(callback, "🔎 Пришли ID (цифры) или @username", _kb([BACK]))


@router.message(AdminState.find, F.text)
async def find_input(message: Message, state: FSMContext):
    text = message.text.strip()
    if text.isdigit():
        person = await get_user(int(text))
    else:
        person = await find_user_by_username(text.lstrip("@").split("/")[-1])
    if not person:
        await message.answer("Не нашёл. Пришли другой ID или @username", reply_markup=_kb([BACK]))
        return
    await state.clear()
    await send_card(message.bot, person)


async def _refresh_card(callback: CallbackQuery, person_id: int, toast: str):
    person = await get_user(person_id)
    if not person:
        await callback.answer("Пользователя уже нет", show_alert=True)
        return
    await callback.answer(toast)
    text = await card_text(person)
    keyboard = card_keyboard(person)
    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("adm:ban:"))
async def cb_ban(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[2])
    if await set_banned(person_id, True):
        try:
            await callback.bot.send_message(person_id, ui.BANNED)
        except Exception:
            pass
    await _refresh_card(callback, person_id, "Забанен")


@router.callback_query(F.data.startswith("adm:unban:"))
async def cb_unban(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[2])
    await set_banned(person_id, False)
    await _refresh_card(callback, person_id, "Разбанен")


@router.callback_query(F.data.startswith("adm:dismiss:"))
async def cb_dismiss(callback: CallbackQuery):
    person_id = int(callback.data.split(":")[2])
    await dismiss_reports(person_id)
    await _refresh_card(callback, person_id, "Жалобы закрыты")


@router.callback_query(F.data.startswith("adm:warn:"))
async def cb_photo_warn(callback: CallbackQuery):
    """Фото без лица или чужое: фото убираем + предупреждение (на третье нарушение — бан)."""
    person_id = int(callback.data.split(":")[2])
    person = await get_user(person_id)
    if not person or not person.get("photo_id"):
        await callback.answer("Фото уже убрано", show_alert=True)
        return
    total = await warn_photo(person_id)
    verdict = await strikes.punish(callback.bot, person_id, total, ui.REASON_PHOTO)
    text = verdict if strikes.is_ban_text(verdict) else f"{ui.PHOTO_WARNING}\n\n{verdict}"
    await _notify(callback.bot, person_id, text)
    await _refresh_card(callback, person_id, "Забанен" if strikes.is_ban_text(verdict) else "Фото убрано, предупреждение ушло")


@router.callback_query(F.data.startswith("adm:badprof:"))
async def cb_bad_profile(callback: CallbackQuery):
    """Неадекватная анкета: скрываем, просим заполнить заново + предупреждение."""
    person_id = int(callback.data.split(":")[2])
    person = await get_user(person_id)
    if not person or not person.get("description"):
        await callback.answer("Анкета уже скрыта", show_alert=True)
        return
    await hide_profile_text(person_id)
    verdict = await strikes.give(callback.bot, person_id, "profile", ui.REASON_PROFILE)
    text = verdict if strikes.is_ban_text(verdict) else f"{ui.PROFILE_HIDDEN}\n\n{verdict}"
    await _notify(callback.bot, person_id, text)
    await _refresh_card(callback, person_id, "Забанен" if strikes.is_ban_text(verdict) else "Анкета скрыта, предупреждение ушло")


async def _notify(bot, person_id: int, text: str):
    try:
        await bot.send_message(person_id, text)
    except Exception:
        pass  # заблокировал бота — ничего страшного


@router.callback_query(F.data.startswith("adm:ok:"))
async def cb_photo_ok(callback: CallbackQuery):
    await _refresh_card(callback, int(callback.data.split(":")[2]), "Ок")


# =========================================================
# ПРОВЕРКА ФОТО
# =========================================================

def profile_flags(person) -> list[str]:
    """Что подозрительного в текстах анкеты: мат и пошлость."""
    flags = []
    texts = [person.get(k) or "" for k in ("full_name", "city", "interests", "description")]
    if any(moderation.is_bad(t) for t in texts):
        flags.append("🤬 В анкете мат или пошлость")
    return flags


async def review_photo(bot, user_id: int, is_new: bool):
    """Каждое новое фото — админу, бан в одну кнопку. Ошибки не мешают пользователю."""
    if user_id == ADMIN_ID:
        return
    try:
        person = await get_user(user_id)
        if person and person.get("photo_id"):
            note = "🆕 <b>Новая анкета</b> — проверь фото" if is_new else "🔄 <b>Сменил(а) фото</b> — проверь"
            note += "".join(f"\n{flag}" for flag in profile_flags(person))
            await send_card(bot, person, note=note, review=True)
    except Exception:
        logging.exception("Не удалось отправить фото на проверку %s", user_id)


# =========================================================
# РАССЫЛКА И ГОЛОСА
# =========================================================

async def bc_text() -> str:
    targets = await broadcast_targets(broadcast.CAMPAIGN)
    no_profile = sum(1 for t in targets if t["age"] is None)
    no_photo = sum(1 for t in targets if t["age"] is not None and not t["photo_id"])
    waiting = sum(1 for t in targets if t["photo_id"] and t["incoming"])
    rest = len(targets) - no_profile - no_photo - waiting
    st = await broadcast_stats(broadcast.CAMPAIGN)
    votes = await vote_stats()
    total_votes = sum(votes.values())
    lines = [
        "📣 <b>Рассылка «что делаем дальше»</b>",
        "",
        "Каждому своя строка + голосование за функцию. Каждому один раз, "
        "забаненным и отписавшимся не уходит",
        "",
        f"Осталось отправить: <b>{len(targets)}</b>",
        f"· без анкеты: {no_profile} · без фото: {no_photo}",
        f"· ждут вайбы: {waiting} · остальные: {rest}",
    ]
    if st:
        lines.append(
            f"Уже ушло: {st.get('sent', 0)} · заблокировали бота: {st.get('blocked', 0)} · "
            f"ошибок: {st.get('error', 0)}"
        )
    if broadcast.is_running():
        lines.append("⏳ Идёт отправка…")
    lines += ["", f"🗳 <b>Голоса</b> ({total_votes})"]
    for key, (label, _) in sorted(ui.FEATURES.items(), key=lambda kv: -votes.get(kv[0], 0)):
        n = votes.get(key, 0)
        lines.append(f"{label}: <b>{n}</b> ({_pct(n, total_votes)})")
    return "\n".join(lines)


def bc_keyboard():
    return _kb(
        [_b("👀 Пример себе", "adm:bc:preview"), _b("🔄 Обновить", "adm:bc")],
        [_b("🚀 Отправить всем", "adm:bc:ask", "primary")],
        [BACK],
    )


@router.callback_query(F.data == "adm:bc")
async def cb_bc(callback: CallbackQuery):
    await _show(callback, await bc_text(), bc_keyboard())


@router.callback_query(F.data == "adm:bc:preview")
async def cb_bc_preview(callback: CallbackQuery):
    """Как увидят разные люди: четыре варианта личной строки."""
    await callback.answer()
    total = (await get_admin_stats())["total_users"]
    username = (await callback.bot.me()).username
    samples = [
        {"age": None, "photo_id": None, "incoming": 0},
        {"age": 20, "photo_id": None, "incoming": 0},
        {"age": 20, "photo_id": "x", "incoming": 3},
        {"age": 20, "photo_id": "x", "incoming": 0},
    ]
    for person in samples:
        await callback.message.answer(
            ui.broadcast_text(person, total),
            reply_markup=broadcast.broadcast_keyboard(person, username),
        )


@router.callback_query(F.data == "adm:bc:ask")
async def cb_bc_ask(callback: CallbackQuery):
    n = len(await broadcast_targets(broadcast.CAMPAIGN))
    await _show(
        callback,
        f"Точно отправить <b>{n}</b> людям? Отменить после старта нельзя",
        _kb([_b(f"✅ Да, отправить {n}", "adm:bc:go", "success")], [_b("← Назад", "adm:bc")]),
    )


@router.callback_query(F.data == "adm:bc:go")
async def cb_bc_go(callback: CallbackQuery):
    if not broadcast.start(callback.bot, ADMIN_ID):
        await callback.answer("Уже отправляется", show_alert=True)
        return
    await _show(callback, await bc_text() + "\n\nИтог пришлю отдельным сообщением", bc_keyboard())


# =========================================================
# «МЫ СНОВА В СТРОЮ»
# =========================================================

async def sorry_text() -> str:
    targets = await broadcast_targets(broadcast.SORRY)
    st = await broadcast_stats(broadcast.SORRY)
    lines = [
        "🙏 <b>Сообщение «Мы снова в строю»</b>",
        "",
        "Одно сообщение всем (кроме забаненных и отписавшихся), каждому один раз. "
        "Кнопка: найти вайб / посмотреть вайбы / заполнить анкету + канал",
        "",
        f"Осталось отправить: <b>{len(targets)}</b>",
    ]
    if st:
        lines.append(
            f"Уже ушло: {st.get('sent', 0)} · заблокировали бота: {st.get('blocked', 0)} · "
            f"ошибок: {st.get('error', 0)}"
        )
    if broadcast.is_running():
        lines.append("⏳ Идёт отправка…")
    return "\n".join(lines)


def sorry_keyboard_admin():
    return _kb(
        [_b("👀 Пример себе", "adm:sorry:preview"), _b("🔄 Обновить", "adm:sorry")],
        [_b("🚀 Отправить всем", "adm:sorry:ask", "primary")],
        [BACK],
    )


@router.callback_query(F.data == "adm:sorry")
async def cb_sorry(callback: CallbackQuery):
    await _show(callback, await sorry_text(), sorry_keyboard_admin())


@router.callback_query(F.data == "adm:sorry:preview")
async def cb_sorry_preview(callback: CallbackQuery):
    await callback.answer()
    username = (await callback.bot.me()).username
    text, keyboard = broadcast.message_for(
        broadcast.SORRY, {"age": 20, "photo_id": "x", "incoming": 0}, 0, username
    )
    await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "adm:sorry:ask")
async def cb_sorry_ask(callback: CallbackQuery):
    n = len(await broadcast_targets(broadcast.SORRY))
    await _show(
        callback,
        f"Точно отправить «Мы снова в строю» <b>{n}</b> людям? Отменить после старта нельзя",
        _kb([_b(f"✅ Да, отправить {n}", "adm:sorry:go", "success")], [_b("← Назад", "adm:sorry")]),
    )


@router.callback_query(F.data == "adm:sorry:go")
async def cb_sorry_go(callback: CallbackQuery):
    if not broadcast.start(callback.bot, ADMIN_ID, broadcast.SORRY):
        await callback.answer("Уже идёт рассылка, дождись итога", show_alert=True)
        return
    await _show(callback, await sorry_text() + "\n\nИтог пришлю отдельным сообщением", sorry_keyboard_admin())


# =========================================================
# ПРОВЕРКА ТЕКСТОВ ВСЕХ АНКЕТ
# =========================================================

@router.callback_query(F.data == "adm:scan")
async def cb_scan(callback: CallbackQuery):
    """Анкеты с матом: карточками с кнопками, не больше LIST_LIMIT за раз."""
    await callback.answer("Проверяю…")
    found = []
    for p in await active_profiles():
        flags = profile_flags(p)
        if flags:
            found.append((p["telegram_id"], flags))
    if not found:
        await callback.message.answer("🧹 Подозрительных анкет не нашёл", reply_markup=_kb([BACK]))
        return
    await callback.message.answer(
        f"🧹 Подозрительных анкет: <b>{len(found)}</b>"
        + (f", показываю первые {LIST_LIMIT}" if len(found) > LIST_LIMIT else "")
    )
    for person_id, flags in found[:LIST_LIMIT]:
        person = await get_user(person_id)
        if person:
            await send_card(callback.bot, person, note="\n".join(flags))
