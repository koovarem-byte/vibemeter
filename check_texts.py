"""Проверка текстов задач и партий (18.11, отзывы беты): лучший ход не должен угадываться по длине.

Запуск: python3 check_texts.py — печатает долю групп, где лучший вариант самый длинный,
и среднее отношение его длины к средней. Норма: доля не выше случайной (1/число вариантов),
отношение 0.85–1.15. Код возврата 1, если хуже.
"""

import sys
import unicodedata

import partii
import puzzles

ORDER = {"!!": 5, "#": 5, "!": 4, "!?": 3, "?!": 2, "?": 1, "??": 0}


def check(groups, label) -> bool:
    longest, ratios, chance = 0, [], 0.0
    for opts in groups:
        lens = [len(o[0]) for o in opts]
        best = max(opts, key=lambda o: ORDER[o[1]])
        if len(best[0]) == max(lens):
            longest += 1
        ratios.append(len(best[0]) / (sum(lens) / len(lens)))
        chance += 1 / len(opts)
    n = len(groups)
    ratio = sum(ratios) / n
    ok = longest <= chance + 1e-9 and 0.85 <= ratio <= 1.15
    print(f"{label}: лучший самый длинный {longest}/{n} (случайно было бы ~{chance:.0f}), "
          f"длина лучшего к средней {ratio:.2f} — {'ок' if ok else 'ПЛОХО'}")
    return ok


def shown_groups(games=200):
    """19.11: в партии видны 3 варианта из пула (partii.shown) — проверяем то, что видит игрок."""
    return [[s["options"][i] for i in partii.shown(g, s, n)]
            for g in range(1, games + 1) for p in partii.PARTII for n, s in enumerate(p["steps"])]


def check_style_cues(groups) -> bool:
    """Проверяет, не выделяется ли лучший ход единственной скобкой, вопросом, эмодзи или длиной."""
    exposed = 0
    for opts in groups:
        best = max(opts, key=lambda o: ORDER[o[1]])
        features = (
            lambda text: ")" in text,
            lambda text: "?" in text,
            lambda text: any(unicodedata.category(ch) == "So" for ch in text),
        )
        for feature in features:
            values = [feature(o[0]) for o in opts]
            if (sum(values) == 1 and feature(best[0])) or (sum(values) == len(values) - 1 and not feature(best[0])):
                exposed += 1
                break
        else:
            lengths = [len(o[0]) for o in opts]
            if len(set(lengths)) == len(lengths) and len(best[0]) == max(lengths):
                exposed += 1
    rate = exposed / len(groups) if groups else 0
    ok = rate <= 0.08
    print(f"Подсказка по оформлению в {exposed}/{len(groups)} видимых троек ({rate:.1%}) — {'ок' if ok else 'ПЛОХО'}")
    return ok


if __name__ == "__main__":
    a = check([p["moves"] for p in puzzles.PUZZLES], "Задачи")
    b = check([s["options"] for p in partii.PARTII for s in p["steps"]], "Партии (весь пул)")
    visible = shown_groups()
    c = check(visible, "Партии (что видно, 200 игр)")
    d = check_style_cues(visible)
    sys.exit(0 if a and b and c and d else 1)
