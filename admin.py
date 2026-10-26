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

import weeklystats
from vibehour import MSK
from config import ADMIN_ID
from database import (
    admin_counts,
    banned_users,
    count_reports,
    dismiss_reports,
    find_user_by_username,
    get_admin_stats,
    get_stats,
    get_user,
    growth_metrics,
    open_reports,
    recent_profiles,
    set_banned,
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
        d1 = "первые цифры завтра"
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
        f"(Mini App и бот без @username)\n"
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
    if about:
        lines += ["", f"<i>{about}</i>"]
    if note:
        lines = [note, ""] + lines
    return "\n".join(lines)


def card_keyboard(person, report=False, review=False):
    pid = person["telegram_id"]
    first = (
        _b("✅ Разбанить", f"adm:unban:{pid}", "success") if person["is_banned"]
        else _b("🚫 Забанить", f"adm:ban:{pid}", "danger")
    )
    rows = [[first]]
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


@router.callback_query(F.data.startswith("adm:ok:"))
async def cb_photo_ok(callback: CallbackQuery):
    await _refresh_card(callback, int(callback.data.split(":")[2]), "Ок")


# =========================================================
# ПРОВЕРКА ФОТО
# =========================================================

async def review_photo(bot, user_id: int, is_new: bool):
    """Каждое новое фото — админу, бан в одну кнопку. Ошибки не мешают пользователю."""
    if user_id == ADMIN_ID:
        return
    try:
        person = await get_user(user_id)
        if person and person.get("photo_id"):
            note = "🆕 <b>Новая анкета</b> — проверь фото" if is_new else "🔄 <b>Сменил(а) фото</b> — проверь"
            await send_card(bot, person, note=note, review=True)
    except Exception:
        logging.exception("Не удалось отправить фото на проверку %s", user_id)
