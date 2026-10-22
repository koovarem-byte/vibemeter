"""Игры на двоих для пар со взаимным вайбом: «Правда или действие» и «Викторина вайба».

Состояние игры — один JSON. Все ходы проходят через apply(), которая чистая:
получает состояние и действие, возвращает новое состояние или код ошибки.
"""

import random

KIND_TRUTH = "truth_dare"
KIND_QUIZ = "quiz"
KINDS = (KIND_TRUTH, KIND_QUIZ)

TITLES = {KIND_TRUTH: "Правда или действие", KIND_QUIZ: "Викторина вайба"}

ROUNDS = 6          # по три хода на каждого
QUIZ_LEN = 5
MAX_TEXT = 300

TRUTHS = [
    "Какая песня у тебя на повторе последние дни?",
    "Что тебя в людях привлекает сильнее всего?",
    "Какое место в мире мечтаешь увидеть?",
    "Какой твой самый неловкий момент, о котором можно рассказать?",
    "Чем ты гордишься, но редко говоришь об этом?",
    "Какой идеальный выходной у тебя выглядит?",
    "Что бы ты сделал(а), если бы завтра можно было не работать и не учиться?",
    "Какой фильм ты пересматривал(а) больше всего раз?",
    "Какое самое спонтанное решение ты принимал(а)?",
    "Что тебя сразу располагает к человеку при знакомстве?",
    "Какая у тебя странная привычка?",
    "О чём ты мечтал(а) в детстве?",
    "Что для тебя значит «своя волна» в общении?",
    "Какой навык ты хотел(а) бы освоить в этом году?",
]

DARES = [
    "Отправь голосовое: расскажи про свой день за 15 секунд",
    "Напиши три слова, которые лучше всего тебя описывают",
    "Назови песню, которую хочешь, чтобы послушал второй игрок, и объясни почему",
    "Придумай прозвище для собеседника по его анкете",
    "Опиши свой идеальный вечер одним предложением без слова «фильм»",
    "Расскажи самую смешную историю из школы или универа в трёх предложениях",
    "Предложи тему для разговора, о которой ты мог(ла) бы говорить час",
    "Отправь эмодзи-описание своего настроения, только из 5 эмодзи",
    "Задай собеседнику вопрос, который хочешь услышать сам(а)",
    "Расскажи, какой комплимент тебе запомнился больше всего",
    "Придумай название для вашей истории знакомства",
    "Опиши собеседника тремя словами по анкете",
]

QUIZ_QUESTIONS = [
    ("Утро или ночь?", "Утро", "Ночь"),
    ("Горы или море?", "Горы", "Море"),
    ("Кофе или чай?", "Кофе", "Чай"),
    ("Кино дома или кинотеатр?", "Дома", "Кинотеатр"),
    ("Планировать или импровизировать?", "Планировать", "Импровизировать"),
    ("Писать или звонить?", "Писать", "Звонить"),
    ("Город или природа?", "Город", "Природа"),
    ("Собака или кот?", "Собака", "Кот"),
    ("Вечеринка или тихий вечер?", "Вечеринка", "Тихий вечер"),
    ("Сладкое или солёное?", "Сладкое", "Солёное"),
    ("Путешествие или уютный дом?", "Путешествие", "Дом"),
    ("Спорт или книги?", "Спорт", "Книги"),
    ("Лето или зима?", "Лето", "Зима"),
    ("Мемы или длинные разговоры?", "Мемы", "Разговоры"),
]


def new_state(kind: str, user_one: int, user_two: int) -> dict:
    if kind == KIND_TRUTH:
        return {
            "turn": user_one, "round": 0, "phase": "choose",
            "pick": None, "prompt": None, "answer": None,
            "used": [], "log": [],
        }
    picked = random.sample(QUIZ_QUESTIONS, QUIZ_LEN)
    return {
        "author": user_one, "guesser": user_two,
        "qs": [{"q": q, "a": a, "b": b} for q, a, b in picked],
        "self": [], "guess": [],
    }


def _other(game, user_id: int) -> int:
    return game["user_two"] if user_id == game["user_one"] else game["user_one"]


def apply(kind: str, game: dict, state: dict, user_id: int, body: dict):
    """(новое состояние, None) или (None, код ошибки). game: user_one/user_two."""
    action = body.get("action")
    s = dict(state)

    if kind == KIND_TRUTH:
        if s["phase"] == "done":
            return None, "finished"

        if s["phase"] == "choose" and action == "choose":
            if s["turn"] != user_id:
                return None, "not_your_turn"
            pick = body.get("pick")
            if pick not in ("truth", "dare"):
                return None, "bad_request"
            pool = TRUTHS if pick == "truth" else DARES
            fresh = [p for p in pool if p not in s["used"]] or pool
            s.update(pick=pick, prompt=random.choice(fresh), phase="answer",
                     used=s["used"] + [])
            s["used"] = s["used"] + [s["prompt"]]
            return s, None

        if s["phase"] == "answer" and action in ("answer", "skip"):
            if s["turn"] != user_id:
                return None, "not_your_turn"
            if action == "skip":
                s["answer"] = None
            else:
                text = str(body.get("text") or "").strip()
                if not text or len(text) > MAX_TEXT:
                    return None, "bad_text"
                s["answer"] = text
            s["phase"] = "rate"
            return s, None

        if s["phase"] == "rate" and action == "rate":
            if s["turn"] == user_id:
                return None, "not_your_turn"
            score = body.get("score")
            if score not in ("fire", "ok"):
                return None, "bad_request"
            s["log"] = s["log"] + [{
                "who": s["turn"], "pick": s["pick"], "prompt": s["prompt"],
                "answer": s["answer"], "score": score,
            }]
            s["round"] += 1
            if s["round"] >= ROUNDS:
                s["phase"] = "done"
            else:
                s.update(turn=_other(game, s["turn"]), phase="choose",
                         pick=None, prompt=None, answer=None)
            return s, None
        return None, "wrong_phase"

    # викторина
    if action != "answer":
        return None, "bad_request"
    choice = body.get("answer")
    if choice not in ("a", "b"):
        return None, "bad_request"
    if len(s["self"]) < QUIZ_LEN:
        if user_id != s["author"]:
            return None, "not_your_turn"
        s["self"] = s["self"] + [choice]
        return s, None
    if len(s["guess"]) < QUIZ_LEN:
        if user_id != s["guesser"]:
            return None, "not_your_turn"
        s["guess"] = s["guess"] + [choice]
        return s, None
    return None, "finished"


def view(kind: str, game: dict, state: dict, user_id: int) -> dict:
    """Что показать игроку. Без лишнего: чужие ответы только когда пора."""
    if kind == KIND_TRUTH:
        s = state
        out = {
            "kind": kind, "phase": s["phase"], "round": s["round"], "rounds": ROUNDS,
            "my_turn": s["turn"] == user_id,
            "pick": s["pick"], "prompt": s["prompt"],
            "log": [{"mine": x["who"] == user_id, "pick": x["pick"], "prompt": x["prompt"],
                     "answer": x["answer"], "score": x["score"]} for x in s["log"]],
        }
        if s["phase"] == "rate":
            out["answer"] = s["answer"]
        if s["phase"] == "answer" and s["turn"] != user_id:
            out["answer"] = None
        return out

    s = state
    me_author = user_id == s["author"]
    done = len(s["guess"]) >= QUIZ_LEN
    if len(s["self"]) < QUIZ_LEN:
        phase = "answer" if me_author else "wait_author"
        index = len(s["self"])
    elif not done:
        phase = "wait_guess" if me_author else "guess"
        index = len(s["guess"])
    else:
        phase, index = "done", QUIZ_LEN
    out = {"kind": kind, "phase": phase, "index": index, "total": QUIZ_LEN,
           "i_am_author": me_author}
    if index < QUIZ_LEN:
        out["question"] = s["qs"][index]
    if done:
        matches = sum(1 for a, b in zip(s["self"], s["guess"]) if a == b)
        out["matches"] = matches
        out["percentage"] = matches * 20
        out["items"] = [{"q": q["q"], "a": q["a"], "b": q["b"], "self": sa, "guess": sg}
                        for q, sa, sg in zip(s["qs"], s["self"], s["guess"])]
    return out
