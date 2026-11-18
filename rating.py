"""Рейтинг «Шах и Чат» — Эло как в шахматах, старт с 0 (17.11, решение владельца).

Каждая задача и партия — «соперник» со своим рейтингом (сложность).
Ожидаемый результат E = 1 / (1 + 10^((R_соперника − R_игрока) / 400)),
новый рейтинг R' = R + K · (S − E), где S — результат 0…1.
Эло зависит только от разницы рейтингов, поэтому шкала с нуля так же честна,
как FIDE: обыграл сложную ситуацию — растёшь сильно, зевнул лёгкую — падаешь.
K (18.11, владелец: «рейтинг медленнее»): новичкам 20 первые 20 игр, дальше 10.
Задача — короткая «блиц-партия» (K вдвое меньше). Ниже нуля рейтинг не падает.
"""

# результат хода (S) по оценке
SCORE = {"!!": 1.0, "#": 1.0, "!": 0.8, "!?": 0.6, "?!": 0.35, "?": 0.15, "??": 0.0}

NEWBIE_GAMES = 20
K_NEWBIE, K_REGULAR = 20, 10

# рейтинг задачи по умолчанию (если в puzzles.py не указан свой)
PUZZLE_RATING = 300


def expected(rating: float, opponent: float) -> float:
    return 1 / (1 + 10 ** ((opponent - rating) / 400))


def k_factor(rated_games: int, blitz: bool = False) -> int:
    k = K_NEWBIE if rated_games < NEWBIE_GAMES else K_REGULAR
    return k // 2 if blitz else k


def update(rating: int, opponent: int, score: float, rated_games: int, blitz: bool = False) -> int:
    new = rating + k_factor(rated_games, blitz) * (score - expected(rating, opponent))
    return max(0, round(new))


def game_score(marks: list[str]) -> float:
    """Результат партии 0…1 — средняя «точность» ходов."""
    vals = [SCORE.get(m, 0.35) for m in marks]
    return sum(vals) / len(vals) if vals else 0.0


def accuracy(marks: list[str]) -> int:
    """Точность в процентах, как в разборе chess.com."""
    return round(game_score(marks) * 100)

NAMES = {"!!": "Бриллиант", "!": "Хороший ход", "!?": "Интересный ход", "?!": "Сомнительно",
         "?": "Ошибка", "??": "Зевок", "#": "Мат"}


def result_of(marks: list[str], mated: bool) -> str:
    """Итог партии: мат (слил), пат (разговор угас) или победа."""
    if mated:
        return "mate"
    s = game_score(marks)
    return "win" if s >= 0.75 else ("stalemate" if s >= 0.45 else "mate")
