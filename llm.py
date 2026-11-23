"""Модель для «Шах и чат»: судья оценивает ход, девушка отвечает, разбор переписки, вопрос автору.

Ключ — ANTHROPIC_API_KEY в переменных хостинга. Нет ключа — available() = False,
и бот показывает режимы без ИИ. Модель — LLM_MODEL (по умолчанию claude-opus-5-5).
Судья и девушка — два отдельных вызова: сначала судья, его оценка подсказывает девушке тон.
"""

import base64
import json
import logging
import os

import anthropic

MODEL = os.getenv("LLM_MODEL", "claude-opus-5-5")
# при отказе модели по безопасности API сам повторит запрос на запасной модели
BETAS = ["server-side-fallback-2026-07-01"]

_client = None


def available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(timeout=60.0, max_retries=2)
    return _client


class LLMError(Exception):
    def __init__(self, message: str, diagnostic: str = "llm_error"):
        super().__init__(message)
        self.diagnostic = diagnostic


async def _call(system: str, content, effort: str = "low", schema: dict | None = None,
                max_tokens: int = 8000) -> str:
    output_config = {"effort": effort}
    if schema:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    try:
        response = await client().beta.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            betas=BETAS,
            fallbacks="default",
            system=system,
            output_config=output_config,
            messages=[{"role": "user", "content": content}],
        )
    except anthropic.APIConnectionError as e:
        raise LLMError("нет связи с моделью", "anthropic_connection") from e
    except anthropic.RateLimitError as e:
        raise LLMError("модель перегружена", "anthropic_rate_limit") from e
    except anthropic.APIStatusError as e:
        # В диагностику попадают только HTTP-код и request ID, без запроса и ключа.
        request_id = (getattr(e, "request_id", None) or "unknown").removeprefix("req_")
        diagnostic = f"anthropic_http_{e.status_code}_req_{request_id}"
        raise LLMError(f"ошибка модели {e.status_code}", diagnostic) from e
    if response.stop_reason == "refusal":
        raise LLMError("модель отказалась", "anthropic_refusal")
    text = next((b.text for b in response.content if b.type == "text"), "").strip()
    if not text:
        raise LLMError("пустой ответ", "anthropic_empty_response")
    return text


# =========================================================
# СУДЬЯ
# =========================================================

RUBRIC = """Значки и оценки:
?? зевок (от -6 до -10): оправдывается («да просто знакомая»); показывает, что ждал («ну наконец-то», «я так ждал»);
отвечает бывшей ночью за минуту и с признанием («нет. о тебе думал»); зовёт гулять, не дав ни одной эмоции;
обижается вслух («понятно», «ладно, не буду мешать»); предъява («ты чего не отвечаешь»).
? слабый ход (от -2 до -5): вопрос-анкета («как дела», «что делаешь»); возвращает тот же вопрос («норм, а у тебя?»);
длинное сообщение на её короткое; объясняет свою шутку.
! хороший ход (от +2 до +5): утверждение вместо вопроса; конкретика про неё (сторис, деталь), а не шаблон; самоирония;
возвращает ход ей («ревнуешь?)»).
!! блестящий ход (от +6 до +10): превращает её выпад в повод встретиться, с местом и временем;
спокойно не реагирует на паузу или проверку и ведёт дальше; коротко, смешно и по ситуации.
# мат в его пользу (+10): ход, после которого она соглашается встретиться или признаёт интерес.
Автоматический минус: грубость, оскорбления, давление, шантаж, манипуляция чувством вины, пошлость —
всегда badge "??", eval -10, coach "так не играем"."""

JUDGE_SYSTEM = f"""Ты оцениваешь один ход парня в учебной переписке как шахматный ход.
Вход: ситуация, вся переписка, последний ход парня.
{RUBRIC}
Поля ответа:
- badge: один из "??", "?", "!", "!!", "#"
- eval: число от -10 до 10, одна цифра после запятой
- coach: одна строка до 12 слов, на «ты», шахматные слова по делу (зевок, инициатива, отдал ферзя, вернул ход), без морали
- finished: true, если партия решилась (она согласилась встретиться, всё слил, разговор умер)
- result: "mate" (он слил, его проверили), "stalemate" (разговор умер), "win" (она согласилась или явно заинтересована) или "none", если не finished
- best_move: лучший ход в этой позиции, коротко, строчными, как в мессенджере (или пустая строка, если его ход и так лучший)
Оценивай строго. Никакого сексуального содержания в best_move."""

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "badge": {"type": "string", "enum": ["??", "?", "!", "!!", "#"]},
        "eval": {"type": "number"},
        "coach": {"type": "string"},
        "finished": {"type": "boolean"},
        "result": {"type": "string", "enum": ["mate", "stalemate", "win", "none"]},
        "best_move": {"type": "string"},
    },
    "required": ["badge", "eval", "coach", "finished", "result", "best_move"],
    "additionalProperties": False,
}

NEUTRAL = {"badge": "?", "eval": 0.0, "coach": "не разобрал ход, засчитал нейтрально",
           "finished": False, "result": "none", "best_move": ""}


def _transcript(history: list[dict]) -> str:
    return "\n".join(f"{'она' if m['who'] == 'her' else 'он'}: {m['text']}" for m in history)


async def judge(situation: dict, history: list[dict], move: str) -> dict:
    """Оценка хода. При сбое — один повтор, потом нейтральная «?» 0 (по ТЗ)."""
    content = (
        f"Ситуация: {situation['context']}\n\n"
        f"Переписка до хода:\n{_transcript(history) or '(пока пусто, он пишет первым)'}\n\n"
        f"Последний ход парня: {move}"
    )
    for _ in range(2):
        try:
            data = json.loads(await _call(JUDGE_SYSTEM, content, effort="medium", schema=JUDGE_SCHEMA))
            data["eval"] = max(-10.0, min(10.0, float(data["eval"])))
            return data
        except (LLMError, ValueError, KeyError, json.JSONDecodeError):
            logging.warning("Судья: не получилось оценить ход, повтор")
    return dict(NEUTRAL)


# =========================================================
# ДЕВУШКА
# =========================================================

def _girl_system(situation: dict) -> str:
    opening = situation.get("opening") or "(первой не пишешь — ждёшь его сообщения)"
    age_voice = (
        "В этой ситуации вы оба подростки 14–17 лет: речь обычная для школы и своего круга, без взрослой лексики про отношения."
        if situation.get("level") == "start" else
        "Говори как взрослая ровесница героя и учитывай конкретный контекст ситуации."
    )
    return f"""Ты — вымышленная собеседница в учебной переписке. Ситуация: {situation['context']}. Твоё первое сообщение: «{opening}».
{age_voice}
Отвечай как в обычном мессенджере: коротко, чаще строчными, без обязательной точки; длину и ритм меняй по ситуации. Иногда уместны «)», «ахах», «хз», но не вставляй их в каждую реплику и не изображай сленг специально.
Реагируй на смысл переписки и свои предыдущие реплики. Не превращай каждый ответ в идеальную шутку, психологический разбор или приглашение продолжить разговор.
Не смотри на оценку судьи и не подстраивайся под неё: отвечай только на то, что действительно написано, с нормальной человеческой неоднозначностью.
Не объясняй свои чувства и не давай советов. Не выходи из роли.
Никакого сексуального содержания. Если собеседник грубит или давит — ответь «всё, пока» и заверши диалог.
Верни только текст реплики."""


async def girl(situation: dict, history: list[dict]) -> str:
    content = f"Переписка:\n{_transcript(history)}\n\nТвоя следующая реплика:"
    text = await _call(_girl_system(situation), content, effort="low", max_tokens=2000)
    return text.strip().strip("«»\"").splitlines()[0][:120]


# =========================================================
# РАЗБОР МОЕЙ ПЕРЕПИСКИ
# =========================================================

RAZBOR_SYSTEM = f"""Ты разбираешь переписку парня с девушкой в формате канала «Шах и чат» — как шахматную партию.
{RUBRIC}
Формат ответа (обычный текст для Telegram, без markdown-разметки звёздочками):
1. «Партия»: каждое его сообщение строкой — «он: текст  значок оценка» (её реплики тоже показывай как «она: текст»).
2. «Главная ошибка:» одна фраза.
3. «Три хода на выбор:» спокойный, наглый, прямой — каждый строкой, и когда какой подходит (коротко).
Правила: имена и ники заменяй на «она»/«он». Ничего не обещай («она согласится», «вернёшь»).
Не учи манипулировать, давить, следить, ревновать ради контроля — на такое отвечай «такое не разбираю. могу помочь с тем, что написать ей самому».
Никакого сексуального содержания. Пиши на «ты», коротко, живо."""


async def razbor(goal: str, text: str | None = None, image: bytes | None = None,
                 media_type: str = "image/jpeg") -> str:
    content = []
    if image:
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": media_type,
            "data": base64.standard_b64encode(image).decode("ascii"),
        }})
    content.append({"type": "text", "text": (
        (f"Переписка:\n{text}\n\n" if text else "Переписка на скриншоте выше.\n\n")
        + f"Чего хочет парень: {goal or 'не написал — разбери в целом'}"
    )})
    return await _call(RAZBOR_SYSTEM, content, effort="medium")


# =========================================================
# ВОПРОС АВТОРУ
# =========================================================

ASK_SYSTEM = """Ты — помощник автора канала «Шах и чат» (разборы переписок как шахматных партий).
Отвечай на вопрос про переписку и общение коротко: 3–6 строк, на «ты», живо, без морали и канцелярита.
Можно предложить 1–2 конкретных хода (что написать). Ничего не обещай.
Не учи манипулировать, давить, следить, взламывать, шантажировать, «заставить» — на такое отвечай:
«такое не разбираю. могу помочь с тем, что написать ей самому».
Никакого сексуального содержания. Ты не психолог — если вопрос про серьёзные проблемы, советуй близких или специалиста."""


async def ask(question: str) -> str:
    return await _call(ASK_SYSTEM, question, effort="low", max_tokens=4000)
