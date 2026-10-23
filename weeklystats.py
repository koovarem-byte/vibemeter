"""Анонимная статистика за неделю — материал для роликов и канала.

Собирает ответы «что выберешь» из вайба дня, игр и тестов с другом.
Только проценты и количества, никаких имён. Мелкие выборки
(меньше MIN_ANSWERS ответов) не показываем: на них проценты врут.
"""

import json
from collections import defaultdict
from datetime import date

from daily import DAILY
from database import week_answers
from games import GAMES
from ui import esc, plural

DAYS = 7
MIN_ANSWERS = 10
TOP = 6


# у вайба дня варианты короткие («Первым» / «Ждать»), добавим сам вопрос
DAILY_QUESTION = {(a, b): text for text, a, b in DAILY}


def _daily_pair(day: date) -> tuple[str, str]:
    _, a, b = DAILY[day.toordinal() % len(DAILY)]
    return a, b


def collect(raw: dict) -> dict:
    """(вариант а, вариант б) → {"a"/"b": {"female"/"male"/None: n}}."""
    stats = defaultdict(lambda: {"a": defaultdict(int), "b": defaultdict(int)})

    for row in raw["daily"]:
        stats[_daily_pair(row["day"])][row["answer"]][row["gender"]] += 1

    for row in raw["games"]:
        try:
            q = json.loads(row["questions_json"])[row["question_index"]]
        except (ValueError, IndexError, TypeError, KeyError):
            continue
        stats[(q["a"], q["b"])][row["answer"]][row["gender"]] += 1

    for row in raw["tests"]:
        for index, answer in zip(json.loads(row["questions"]), row["answers"]):
            q = GAMES[index]
            stats[(q["a"], q["b"])][answer][row["gender"]] += 1

    return stats


def _pct(part: int, whole: int) -> int:
    return round(part * 100 / whole) if whole else 0


def report(stats: dict, totals: dict) -> str:
    lines = [
        "📊 <b>Неделя в Вайбометре</b> (анонимно)",
        "",
        f"Новых анкет: {totals['new_profiles']} · взаимных вайбов: {totals['mutual']}",
        f"Игр: {totals['games']} · пройдено тестов с другом: {totals['tests']}",
    ]

    rows = []
    for (a, b), votes in stats.items():
        na, nb = sum(votes["a"].values()), sum(votes["b"].values())
        if na + nb >= MIN_ANSWERS:
            rows.append((na + nb, a, b, votes, na, nb))
    rows.sort(reverse=True)

    if not rows:
        lines += ["", f"Пока мало ответов: нужно хотя бы {MIN_ANSWERS} на вопрос"]
        return "\n".join(lines)

    facts = []
    lines += ["", "<b>Что выбирают</b>"]
    for total, a, b, votes, na, nb in rows[:TOP]:
        win, lose, nw = (a, b, na) if na >= nb else (b, a, nb)
        key = "a" if win == a else "b"
        question = DAILY_QUESTION.get((a, b))
        answers = f"{total} {plural(total, 'ответ', 'ответа', 'ответов')}"
        if question:
            lines.append(f"• {esc(question)} {esc(win)} — {_pct(nw, total)}% ({answers})")
        elif na == nb:
            lines.append(f"• {esc(a)} и {esc(b)} — поровну ({answers})")
        else:
            lines.append(f"• {esc(win)} — {_pct(nw, total)}% против {esc(lose)} ({answers})")

        split = []
        for gender, label in (("female", "девушки"), ("male", "парни")):
            g_total = votes["a"][gender] + votes["b"][gender]
            if g_total >= MIN_ANSWERS // 2:
                split.append(f"{label}: {_pct(votes[key][gender], g_total)}%")
        if split:
            lines.append(f"   {' · '.join(split)} за «{esc(win)}»")

        pct = _pct(nw, total)
        if pct >= 60 and question:
            facts.append((pct, f"{esc(question)} {pct}% ответили «{esc(win)}»"))
        elif pct >= 60:
            facts.append((pct, f"{pct}% выбрали «{esc(win)}», а не «{esc(lose)}»"))

    # в ролики — самые перекошенные ответы, 50 на 50 никому не интересно
    facts.sort(reverse=True)
    if facts:
        lines += ["", "<b>Готовые фразы для роликов</b>"] + [f"— {f}" for _, f in facts[:3]]
    return "\n".join(lines)


async def build() -> str:
    raw = await week_answers(DAYS)
    return report(collect(raw), raw["totals"])
