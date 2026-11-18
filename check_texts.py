"""Проверка текстов задач и партий (18.11, отзывы беты): лучший ход не должен угадываться по длине.

Запуск: python3 check_texts.py — печатает долю групп, где лучший вариант самый длинный,
и среднее отношение его длины к средней. Норма: доля не выше случайной (1/число вариантов),
отношение 0.85–1.15. Код возврата 1, если хуже.
"""

import sys

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
    ok = longest <= chance and 0.85 <= ratio <= 1.15
    print(f"{label}: лучший самый длинный {longest}/{n} (случайно было бы ~{chance:.0f}), "
          f"длина лучшего к средней {ratio:.2f} — {'ок' if ok else 'ПЛОХО'}")
    return ok


if __name__ == "__main__":
    a = check([p["moves"] for p in puzzles.PUZZLES], "Задачи")
    b = check([s["options"] for p in partii.PARTII for s in p["steps"]], "Партии")
    sys.exit(0 if a and b else 1)
