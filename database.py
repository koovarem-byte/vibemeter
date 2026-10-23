import asyncio
import json
import logging
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
_pool = None


async def get_pool():
    global _pool

    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError("Переменная DATABASE_URL не задана")

        # Соединение с Neon иногда рвётся или подвисает
        # на подключении, поэтому пробуем несколько раз.
        for attempt in range(1, 6):
            try:
                _pool = await asyncpg.create_pool(
                    dsn=DATABASE_URL,
                    min_size=1,
                    max_size=5,
                    command_timeout=30,
                    timeout=15,
                    ssl="require",
                )
                break
            except (OSError, asyncio.TimeoutError, asyncpg.PostgresConnectionError) as e:
                if attempt == 5:
                    raise
                logging.warning(
                    "Neon: попытка %s не удалась (%s), повторяю",
                    attempt, type(e).__name__,
                )
                await asyncio.sleep(attempt * 2)

    return _pool


async def close_db():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def init_db():
    db = await get_pool()

    async with db.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                age INTEGER,
                city TEXT,
                interests TEXT,
                description TEXT,
                photo_id TEXT,
                balance INTEGER DEFAULT 0,
                gender TEXT,
                search_gender TEXT DEFAULT 'all',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS gender TEXT
        """)
        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS search_gender TEXT DEFAULT 'all'
        """)
        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_banned BOOLEAN NOT NULL DEFAULT FALSE
        """)
        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS streak_days INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS best_streak INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS last_active DATE
        """)
        # Вайб-час: кто сейчас в сети и можно ли напоминать
        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS last_seen TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS vibe_hour_notify BOOLEAN NOT NULL DEFAULT TRUE
        """)
        # Служебные отметки (например, в какой день уже напомнили о вайб-часе)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id BIGSERIAL PRIMARY KEY,
                from_user BIGINT NOT NULL,
                to_user BIGINT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user, to_user)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id BIGSERIAL PRIMARY KEY,
                from_user BIGINT NOT NULL,
                to_user BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user, to_user)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS skips (
                id BIGSERIAL PRIMARY KEY,
                from_user BIGINT NOT NULL,
                to_user BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user, to_user)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS blocks (
                id BIGSERIAL PRIMARY KEY,
                from_user BIGINT NOT NULL,
                to_user BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user, to_user)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id BIGSERIAL PRIMARY KEY,
                from_user BIGINT NOT NULL,
                to_user BIGINT NOT NULL,
                text TEXT NOT NULL,
                answer TEXT,
                answered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                answered_at TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id BIGSERIAL PRIMARY KEY,
                user_one BIGINT NOT NULL,
                user_two BIGINT NOT NULL,
                game_type TEXT NOT NULL DEFAULT 'vibe',
                question TEXT,
                answer_one TEXT,
                answer_two TEXT,
                status TEXT DEFAULT 'waiting',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                questions_json TEXT
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_answers (
                user_id BIGINT NOT NULL,
                day DATE NOT NULL,
                answer TEXT NOT NULL CHECK (answer IN ('a', 'b')),
                PRIMARY KEY (user_id, day)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS duo_games (
                id BIGSERIAL PRIMARY KEY,
                kind TEXT NOT NULL,
                user_one BIGINT NOT NULL,
                user_two BIGINT NOT NULL,
                state JSONB NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'active',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # «Тайная симпатия»: кого человек отметил по @username (в нижнем регистре)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS secret_crushes (
                from_user BIGINT NOT NULL,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (from_user, username)
            )
        """)

        # «Проверь вайб с другом»: тест автора и ответы друзей
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS vibe_tests (
                code TEXT PRIMARY KEY,
                owner_id BIGINT NOT NULL,
                owner_name TEXT,
                questions TEXT NOT NULL,
                answers TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS vibe_test_answers (
                code TEXT NOT NULL REFERENCES vibe_tests(code) ON DELETE CASCADE,
                user_id BIGINT NOT NULL,
                name TEXT,
                answers TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (code, user_id)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                invitee BIGINT PRIMARY KEY,
                inviter BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS game_answers (
                id BIGSERIAL PRIMARY KEY,
                game_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                question_index INTEGER NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_id, user_id, question_index)
            )
        """)


# DUO GAMES (правда или действие, викторина)

def _duo(row):
    if row is None:
        return None
    d = dict(row)
    if isinstance(d["state"], str):
        d["state"] = json.loads(d["state"])
    return d


async def create_duo(kind: str, user_one: int, user_two: int, state: dict):
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO duo_games (kind, user_one, user_two, state)
            VALUES ($1, $2, $3, $4::jsonb) RETURNING *
        """, kind, user_one, user_two, json.dumps(state))
    return _duo(row)


async def get_duo(duo_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        return _duo(await conn.fetchrow("SELECT * FROM duo_games WHERE id = $1", duo_id))


async def find_active_duo(kind: str, a: int, b: int):
    db = await get_pool()
    async with db.acquire() as conn:
        return _duo(await conn.fetchrow("""
            SELECT * FROM duo_games
            WHERE kind = $1 AND status = 'active'
              AND ((user_one = $2 AND user_two = $3) OR (user_one = $3 AND user_two = $2))
              AND updated_at > now() - interval '7 days'
            ORDER BY id DESC LIMIT 1
        """, kind, a, b))


async def list_duos(user_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM duo_games
            WHERE (user_one = $1 OR user_two = $1)
              AND updated_at > now() - interval '7 days'
            ORDER BY updated_at DESC LIMIT 20
        """, user_id)
    return [_duo(r) for r in rows]


async def mutate_duo(duo_id: int, fn):
    """Блокирует строку, зовёт fn(game, state) -> (новое состояние, статус, ошибка)."""
    db = await get_pool()
    async with db.acquire() as conn:
        async with conn.transaction():
            row = _duo(await conn.fetchrow(
                "SELECT * FROM duo_games WHERE id = $1 FOR UPDATE", duo_id))
            if row is None:
                return None, "not_found", None
            state, status, err = fn(row, row["state"])
            if err:
                return row, err, None
            await conn.execute("""
                UPDATE duo_games SET state = $2::jsonb, status = $3, updated_at = now()
                WHERE id = $1
            """, duo_id, json.dumps(state), status)
            row["state"], row["status"] = state, status
            return row, None, state


# REFERRALS

async def add_referral(invitee: int, inviter: int) -> bool:
    """Запоминает, кто позвал. Себя звать нельзя, пригласитель должен существовать."""
    if invitee == inviter:
        return False
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO referrals (invitee, inviter)
            SELECT $1, telegram_id FROM users WHERE telegram_id = $2
            ON CONFLICT DO NOTHING
            RETURNING invitee
        """, invitee, inviter)
    return row is not None


async def get_inviter(invitee: int) -> int | None:
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval(
            "SELECT inviter FROM referrals WHERE invitee = $1", invitee
        )


async def count_referrals(inviter: int) -> int:
    """Друзья, которые дошли до готовой анкеты с фото."""
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval("""
            SELECT COUNT(*) FROM referrals r
            JOIN users u ON u.telegram_id = r.invitee
            WHERE r.inviter = $1 AND u.age IS NOT NULL AND u.photo_id IS NOT NULL
        """, inviter)


# DAILY VIBE

async def get_daily_answers(user_ids: list[int]) -> dict[int, str]:
    """Ответы на вайб дня за сегодня (по Москве): {user_id: 'a'|'b'}."""
    if not user_ids:
        return {}
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT user_id, answer FROM daily_answers
            WHERE user_id = ANY($1::bigint[])
              AND day = (now() AT TIME ZONE 'Europe/Moscow')::date
        """, user_ids)
    return {r["user_id"]: r["answer"] for r in rows}


async def set_daily_answer(user_id: int, answer: str) -> bool:
    """Один ответ в день. False, если уже отвечал."""
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO daily_answers (user_id, day, answer)
            VALUES ($1, (now() AT TIME ZONE 'Europe/Moscow')::date, $2)
            ON CONFLICT DO NOTHING
            RETURNING user_id
        """, user_id, answer)
    return row is not None


# USERS

async def get_user(telegram_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM users WHERE telegram_id = $1",
            telegram_id,
        )


async def create_user(
    telegram_id: int,
    username: str | None = None,
    full_name: str | None = None,
):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (telegram_id, username, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (telegram_id) DO NOTHING
        """, telegram_id, username, full_name)


async def update_user(
    telegram_id: int,
    username: str | None = None,
    full_name: str | None = None,
    age: int | None = None,
    city: str | None = None,
    interests: str | None = None,
    description: str | None = None,
    photo_id: str | None = None,
    gender: str | None = None,
    search_gender: str | None = None,
):
    data = {
        "username": username,
        "full_name": full_name,
        "age": age,
        "city": city,
        "interests": interests,
        "description": description,
        "photo_id": photo_id,
        "gender": gender,
        "search_gender": search_gender,
    }

    fields = [(k, v) for k, v in data.items() if v is not None]

    if not fields:
        return

    assignments = [
        f"{field} = ${i}"
        for i, (field, _) in enumerate(fields, start=2)
    ]
    values = [telegram_id] + [v for _, v in fields]

    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            f"UPDATE users SET {', '.join(assignments)} "
            "WHERE telegram_id = $1",
            *values,
        )


async def delete_user(telegram_id: int):
    db = await get_pool()

    async with db.acquire() as conn:
        async with conn.transaction():
            for table in ("likes", "skips", "blocks"):
                await conn.execute(
                    f"DELETE FROM {table} "
                    "WHERE from_user = $1 OR to_user = $1",
                    telegram_id,
                )

            await conn.execute(
                "DELETE FROM questions "
                "WHERE from_user = $1 OR to_user = $1",
                telegram_id,
            )
            await conn.execute(
                "DELETE FROM game_answers WHERE user_id = $1",
                telegram_id,
            )
            await conn.execute(
                "DELETE FROM games WHERE user_one = $1 OR user_two = $1",
                telegram_id,
            )
            await conn.execute(
                "DELETE FROM secret_crushes WHERE from_user = $1",
                telegram_id,
            )
            await conn.execute(
                "DELETE FROM vibe_test_answers WHERE user_id = $1",
                telegram_id,
            )
            await conn.execute(
                "DELETE FROM vibe_tests WHERE owner_id = $1",
                telegram_id,
            )
            await conn.execute(
                "DELETE FROM users WHERE telegram_id = $1",
                telegram_id,
            )


# LIKES

async def add_like(from_user: int, to_user: int) -> bool:
    """True, если лайк новый."""
    db = await get_pool()
    async with db.acquire() as conn:
        result = await conn.execute("""
            INSERT INTO likes (from_user, to_user)
            VALUES ($1, $2)
            ON CONFLICT (from_user, to_user) DO NOTHING
        """, from_user, to_user)
        return result.endswith(" 1")


async def has_like(from_user: int, to_user: int):
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM likes
                WHERE from_user = $1 AND to_user = $2
            )
        """, from_user, to_user)


async def is_liked(from_user: int, to_user: int):
    return await has_like(from_user, to_user)


# SKIPS

async def add_skip(from_user: int, to_user: int):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute("""
            INSERT INTO skips (from_user, to_user)
            VALUES ($1, $2)
            ON CONFLICT (from_user, to_user) DO NOTHING
        """, from_user, to_user)


async def delete_skip(from_user: int, to_user: int) -> bool:
    """«Вернуть» анкету после «Мимо». True, если было что вернуть."""
    db = await get_pool()
    async with db.acquire() as conn:
        result = await conn.execute("""
            DELETE FROM skips WHERE from_user = $1 AND to_user = $2
        """, from_user, to_user)
        return result.endswith(" 1")


async def add_block(from_user: int, to_user: int):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO blocks (from_user, to_user)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            """,
            from_user, to_user,
        )


async def get_blocked_users(telegram_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.telegram_id, u.full_name, u.age, u.city
            FROM blocks b
            JOIN users u ON u.telegram_id = b.to_user
            WHERE b.from_user = $1
            ORDER BY u.full_name
        """, telegram_id)

        return [dict(row) for row in rows]


async def is_blocked(from_user: int, to_user: int):
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM blocks
                WHERE from_user = $1 AND to_user = $2
            )
        """, from_user, to_user)


# CANDIDATES

async def get_candidates(user_id: int):
    db = await get_pool()

    async with db.acquire() as conn:
        current = await conn.fetchrow("""
            SELECT age, search_gender
            FROM users WHERE telegram_id = $1
        """, user_id)

        # Бот только для 18+
        if not current or current["age"] is None or current["age"] < 18:
            return []

        gender_condition = ""
        search_gender = current["search_gender"] or "all"

        if search_gender == "male":
            gender_condition = "AND u.gender = 'male'"
        elif search_gender == "female":
            gender_condition = "AND u.gender = 'female'"

        return await conn.fetch(f"""
            SELECT u.*
            FROM users u
            WHERE u.telegram_id != $1
              AND u.age IS NOT NULL
              AND u.photo_id IS NOT NULL
              AND u.age >= 18
              AND NOT u.is_banned
              {gender_condition}
              AND NOT EXISTS (
                  SELECT 1 FROM likes l
                  WHERE l.from_user = $1
                    AND l.to_user = u.telegram_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM skips s
                  WHERE s.from_user = $1
                    AND s.to_user = u.telegram_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM blocks b
                  WHERE (b.from_user = $1 AND b.to_user = u.telegram_id)
                     OR (b.from_user = u.telegram_id AND b.to_user = $1)
              )
            ORDER BY RANDOM()
        """, user_id)


# INCOMING LIKES

async def get_incoming_likes(user_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetch("""
            SELECT u.*
            FROM users u
            JOIN likes l ON l.from_user = u.telegram_id
            WHERE l.to_user = $1
              AND NOT u.is_banned
              AND NOT EXISTS (
                  SELECT 1 FROM likes r
                  WHERE r.from_user = $1 AND r.to_user = u.telegram_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM skips s
                  WHERE s.from_user = $1 AND s.to_user = u.telegram_id
              )
              AND NOT EXISTS (
                  SELECT 1 FROM blocks b
                  WHERE (b.from_user = $1 AND b.to_user = u.telegram_id)
                     OR (b.from_user = u.telegram_id AND b.to_user = $1)
              )
            ORDER BY l.created_at DESC
        """, user_id)


async def get_mutual_likes(user_id: int, limit: int = 50):
    """Люди со взаимным вайбом, свежие сверху."""
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetch("""
            SELECT u.*
            FROM likes mine
            JOIN likes theirs
              ON theirs.from_user = mine.to_user AND theirs.to_user = $1
            JOIN users u ON u.telegram_id = mine.to_user
            WHERE mine.from_user = $1
              AND NOT u.is_banned
              AND NOT EXISTS (
                  SELECT 1 FROM blocks b
                  WHERE (b.from_user = $1 AND b.to_user = u.telegram_id)
                     OR (b.from_user = u.telegram_id AND b.to_user = $1)
              )
            ORDER BY GREATEST(mine.created_at, theirs.created_at) DESC
            LIMIT $2
        """, user_id, limit)


# REPORTS / BANS

async def add_report(from_user: int, to_user: int, reason: str) -> bool:
    """Жалоба + блокировка для автора. False, если уже жаловался."""
    db = await get_pool()
    async with db.acquire() as conn:
        report_id = await conn.fetchval("""
            INSERT INTO reports (from_user, to_user, reason)
            VALUES ($1, $2, $3)
            ON CONFLICT (from_user, to_user) DO NOTHING
            RETURNING id
        """, from_user, to_user, reason)
        await conn.execute("""
            INSERT INTO blocks (from_user, to_user)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
        """, from_user, to_user)
        return report_id is not None


async def count_reports(to_user: int) -> int:
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval(
            "SELECT COUNT(*) FROM reports WHERE to_user = $1",
            to_user,
        )


async def set_banned(telegram_id: int, banned: bool) -> bool:
    """True, если пользователь найден."""
    db = await get_pool()
    async with db.acquire() as conn:
        result = await conn.execute(
            "UPDATE users SET is_banned = $2 WHERE telegram_id = $1",
            telegram_id, banned,
        )
        if banned:
            await conn.execute(
                "UPDATE reports SET status = 'banned' WHERE to_user = $1 AND status = 'open'",
                telegram_id,
            )
        return result.endswith(" 1")


async def dismiss_reports(to_user: int):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE reports SET status = 'dismissed' WHERE to_user = $1 AND status = 'open'",
            to_user,
        )


async def touch_user(telegram_id: int, username: str | None = None):
    """
    Отмечает активность за сегодня (по Москве) и считает серию дней.
    username: актуальный @username из Telegram ("" — у человека его нет,
    None — не трогать).
    Возвращает None, если пользователя нет, иначе запись:
    is_banned, streak_days, first_today.
    """
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchrow("""
            WITH d AS (
                SELECT (now() AT TIME ZONE 'Europe/Moscow')::date AS today
            ),
            old AS (
                SELECT telegram_id, last_active, streak_days
                FROM users WHERE telegram_id = $1
            ),
            calc AS (
                SELECT old.telegram_id, d.today,
                       old.last_active IS DISTINCT FROM d.today AS first_today,
                       CASE
                           WHEN old.last_active = d.today THEN old.streak_days
                           WHEN old.last_active = d.today - 1 THEN old.streak_days + 1
                           ELSE 1
                       END AS streak
                FROM old, d
            )
            UPDATE users u
            SET streak_days = calc.streak,
                best_streak = GREATEST(u.best_streak, calc.streak),
                last_active = calc.today,
                last_seen = now(),
                username = COALESCE($2, u.username)
            FROM calc
            WHERE u.telegram_id = calc.telegram_id
            RETURNING u.is_banned, u.streak_days, calc.first_today
        """, telegram_id, username)


async def is_banned(telegram_id: int) -> bool:
    db = await get_pool()
    async with db.acquire() as conn:
        return bool(await conn.fetchval(
            "SELECT is_banned FROM users WHERE telegram_id = $1",
            telegram_id,
        ))


# QUESTIONS

async def add_question(from_user: int, to_user: int, text: str):
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval("""
            INSERT INTO questions (from_user, to_user, text)
            VALUES ($1, $2, $3)
            RETURNING id
        """, from_user, to_user, text)


async def get_question(question_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM questions WHERE id = $1",
            question_id,
        )


async def answer_question(question_id: int, answer: str):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute("""
            UPDATE questions
            SET answer = $1, answered = 1, answered_at = CURRENT_TIMESTAMP
            WHERE id = $2 AND answered = 0
        """, answer, question_id)


# GAMES

async def create_game(
    user_one: int,
    user_two: int,
    questions_json: str,
):
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval("""
            INSERT INTO games (
                user_one, user_two, game_type,
                question, questions_json, status
            )
            VALUES ($1, $2, 'vibe', '', $3, 'waiting')
            RETURNING id
        """, user_one, user_two, questions_json)


async def get_latest_game(user_id: int):
    """Последняя игра пользователя (для Mini App)."""
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchrow("""
            SELECT * FROM games
            WHERE user_one = $1 OR user_two = $1
            ORDER BY id DESC
            LIMIT 1
        """, user_id)


async def abandon_game(game_id: int):
    """Бросить игру (статус не 'finished', в статистику не попадёт)."""
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE games SET status = 'abandoned' "
            "WHERE id = $1 AND status = 'waiting'",
            game_id,
        )


async def get_game(game_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM games WHERE id = $1",
            game_id,
        )


async def add_game_answer(
    game_id: int,
    user_id: int,
    question_index: int,
    answer: str,
):
    db = await get_pool()

    async with db.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO game_answers (
                    game_id, user_id, question_index, answer
                )
                VALUES ($1, $2, $3, $4)
            """, game_id, user_id, question_index, answer)

            return True

        except asyncpg.UniqueViolationError:
            return False


async def get_game_answers(game_id: int, user_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM game_answers
            WHERE game_id = $1 AND user_id = $2
            ORDER BY question_index
        """, game_id, user_id)


async def finish_game(game_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE games SET status = 'finished' WHERE id = $1",
            game_id,
        )

# STATISTICS

async def get_stats(user_id: int):
    db = await get_pool()

    async with db.acquire() as conn:
        likes_sent = await conn.fetchval(
            "SELECT COUNT(*) FROM likes WHERE from_user = $1", user_id
        )
        likes_received = await conn.fetchval(
            "SELECT COUNT(*) FROM likes WHERE to_user = $1", user_id
        )
        skips = await conn.fetchval(
            "SELECT COUNT(*) FROM skips WHERE from_user = $1", user_id
        )
        blocks = await conn.fetchval(
            "SELECT COUNT(*) FROM blocks WHERE from_user = $1", user_id
        )
        questions_received = await conn.fetchval(
            "SELECT COUNT(*) FROM questions WHERE to_user = $1", user_id
        )
        questions_sent = await conn.fetchval(
            "SELECT COUNT(*) FROM questions WHERE from_user = $1", user_id
        )
        games = await conn.fetchval("""
            SELECT COUNT(*) FROM games
            WHERE (user_one = $1 OR user_two = $1)
              AND status = 'finished'
        """, user_id)
        mutual_likes = await conn.fetchval("""
            SELECT COUNT(*) FROM likes
            WHERE from_user = $1
              AND to_user IN (
                  SELECT from_user FROM likes WHERE to_user = $1
              )
        """, user_id)

        referrals = await conn.fetchval("""
            SELECT COUNT(*) FROM referrals r
            JOIN users u ON u.telegram_id = r.invitee
            WHERE r.inviter = $1 AND u.age IS NOT NULL AND u.photo_id IS NOT NULL
        """, user_id)

        streaks = await conn.fetchrow(
            "SELECT streak_days, best_streak FROM users WHERE telegram_id = $1",
            user_id,
        )

        return {
            "streak_days": streaks["streak_days"] if streaks else 0,
            "best_streak": streaks["best_streak"] if streaks else 0,
            "likes_sent": likes_sent,
            "likes_received": likes_received,
            "skips": skips,
            "blocks": blocks,
            "questions_received": questions_received,
            "questions_sent": questions_sent,
            "games": games,
            "mutual_likes": mutual_likes,
            "referrals": referrals,
        }
async def get_admin_stats():
    db = await get_pool()

    async with db.acquire() as conn:
        total_users = await conn.fetchval(
            "SELECT COUNT(*) FROM users"
        )

        profiles = await conn.fetchval("""
            SELECT COUNT(*)
            FROM users
            WHERE age IS NOT NULL
              AND city IS NOT NULL
              AND interests IS NOT NULL
              AND description IS NOT NULL
              AND photo_id IS NOT NULL
        """)

        photos = await conn.fetchval(
            "SELECT COUNT(*) FROM users WHERE photo_id IS NOT NULL"
        )

        likes = await conn.fetchval(
            "SELECT COUNT(*) FROM likes"
        )

        skips = await conn.fetchval(
            "SELECT COUNT(*) FROM skips"
        )

        mutual = await conn.fetchval("""
            SELECT COUNT(*)
            FROM likes l1
            WHERE EXISTS (
                SELECT 1
                FROM likes l2
                WHERE l2.from_user = l1.to_user
                  AND l2.to_user = l1.from_user
            )
        """)

        questions = await conn.fetchval(
            "SELECT COUNT(*) FROM questions"
        )

        games = await conn.fetchval(
            "SELECT COUNT(*) FROM games"
        )

        today = await conn.fetchval("""
            SELECT COUNT(*)
            FROM users
            WHERE created_at::date = CURRENT_DATE
        """)

        return {
            "total_users": total_users,
            "profiles": profiles,
            "photos": photos,
            "likes": likes,
            "mutual": mutual // 2,
            "skips": skips,
            "questions": questions,
            "games": games,
            "today": today,
        }


# =========================================================
# VIBE TESTS («Проверь вайб с другом»)
# =========================================================

async def create_vibe_test(code: str, owner_id: int, owner_name: str, questions: list[int], answers: str):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute("""
            INSERT INTO vibe_tests (code, owner_id, owner_name, questions, answers)
            VALUES ($1, $2, $3, $4, $5)
        """, code, owner_id, owner_name, json.dumps(questions), answers)


async def get_vibe_test(code: str):
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM vibe_tests WHERE code = $1", code)
    if not row:
        return None
    test = dict(row)
    test["questions"] = json.loads(test["questions"])
    return test


async def get_vibe_test_answers(code: str):
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT user_id, name, answers, created_at
            FROM vibe_test_answers
            WHERE code = $1
            ORDER BY created_at DESC
            LIMIT 50
        """, code)
    return [dict(r) for r in rows]


async def get_vibe_test_answer(code: str, user_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM vibe_test_answers WHERE code = $1 AND user_id = $2",
            code, user_id,
        )
    return dict(row) if row else None


async def add_vibe_test_answer(code: str, user_id: int, name: str, answers: str) -> bool:
    """Ответ друга. Второй раз пройти тот же тест нельзя."""
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO vibe_test_answers (code, user_id, name, answers)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
            RETURNING user_id
        """, code, user_id, name, answers)
    return row is not None


# =========================================================
# SECRET CRUSHES («Тайная симпатия»)
# =========================================================

async def add_crush(from_user: int, username: str, limit: int) -> str:
    """'added', 'exists' или 'limit'. username уже нормализован."""
    db = await get_pool()
    async with db.acquire() as conn:
        async with conn.transaction():
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM secret_crushes WHERE from_user = $1", from_user
            )
            exists = await conn.fetchval(
                "SELECT 1 FROM secret_crushes WHERE from_user = $1 AND username = $2",
                from_user, username,
            )
            if exists:
                return "exists"
            if count >= limit:
                return "limit"
            await conn.execute(
                "INSERT INTO secret_crushes (from_user, username) VALUES ($1, $2)",
                from_user, username,
            )
    return "added"


async def remove_crush(from_user: int, username: str):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            "DELETE FROM secret_crushes WHERE from_user = $1 AND username = $2",
            from_user, username,
        )


async def list_crushes(from_user: int):
    """Мои отметки; mutual_id — id человека, если симпатия взаимная."""
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.username, t.telegram_id AS mutual_id, t.full_name AS mutual_name
            FROM secret_crushes c
            JOIN users me ON me.telegram_id = c.from_user
            LEFT JOIN users t
                   ON lower(t.username) = c.username
                  AND t.is_banned IS NOT TRUE
                  AND EXISTS (
                      SELECT 1 FROM secret_crushes back
                      WHERE back.from_user = t.telegram_id
                        AND back.username = lower(me.username)
                  )
            WHERE c.from_user = $1
            ORDER BY c.created_at
        """, from_user)
    return [dict(r) for r in rows]


async def find_mutual_crush(from_user: int, username: str):
    """Человек с этим @username, если он тоже отметил from_user."""
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT t.*
            FROM users t, users me
            WHERE me.telegram_id = $1
              AND lower(t.username) = $2
              AND t.telegram_id <> me.telegram_id
              AND t.is_banned IS NOT TRUE
              AND me.username IS NOT NULL AND me.username <> ''
              AND EXISTS (
                  SELECT 1 FROM secret_crushes back
                  WHERE back.from_user = t.telegram_id
                    AND back.username = lower(me.username)
              )
        """, from_user, username)
    return dict(row) if row else None


# =========================================================
# ВАЙБ-ЧАС
# =========================================================

async def mark_seen(telegram_id: int):
    """Отметка «в сети» из Mini App, не чаще раза в минуту."""
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute("""
            UPDATE users SET last_seen = now()
            WHERE telegram_id = $1
              AND (last_seen IS NULL OR last_seen < now() - interval '1 minute')
        """, telegram_id)


async def count_online(minutes: int) -> int:
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval("""
            SELECT COUNT(*) FROM users
            WHERE age IS NOT NULL AND NOT is_banned
              AND last_seen > now() - make_interval(mins => $1)
        """, minutes)


async def claim_once(key: str, value: str) -> bool:
    """True только для первого, кто записал value: защита от двойной рассылки."""
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO app_state (key, value) VALUES ($1, $2)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            WHERE app_state.value <> EXCLUDED.value
            RETURNING key
        """, key, value)
    return row is not None


async def vibe_hour_recipients(days: int) -> list[int]:
    """Кому напоминать: анкета есть, не забанен, не отключал, заходил недавно."""
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT telegram_id FROM users
            WHERE age IS NOT NULL AND NOT is_banned AND vibe_hour_notify
              AND last_active >= (now() AT TIME ZONE 'Europe/Moscow')::date - $1::int
        """, days)
    return [r["telegram_id"] for r in rows]


async def set_vibe_hour_notify(telegram_id: int, value: bool):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE users SET vibe_hour_notify = $2 WHERE telegram_id = $1",
            telegram_id, value,
        )


# =========================================================
# ПРОГРЕСС ГОРОДА
# =========================================================

async def city_counts() -> list[tuple[str, int]]:
    """Сколько анкет в каждом городе (как написали, без нормализации)."""
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT city, COUNT(*) AS n FROM users
            WHERE age IS NOT NULL AND NOT is_banned AND city IS NOT NULL
            GROUP BY city
        """)
    return [(r["city"], r["n"]) for r in rows]
