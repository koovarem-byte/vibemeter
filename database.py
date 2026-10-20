import asyncio
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
                "DELETE FROM users WHERE telegram_id = $1",
                telegram_id,
            )


# LIKES

async def add_like(from_user: int, to_user: int):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute("""
            INSERT INTO likes (from_user, to_user)
            VALUES ($1, $2)
            ON CONFLICT (from_user, to_user) DO NOTHING
        """, from_user, to_user)


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


async def get_pending_questions(user_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM questions
            WHERE to_user = $1 AND answered = 0
            ORDER BY created_at DESC
        """, user_id)


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
        mutual_likes = await conn.fetchval("""
            SELECT COUNT(*) FROM likes
            WHERE from_user = $1
              AND to_user IN (
                  SELECT from_user FROM likes WHERE to_user = $1
              )
        """, user_id)

        return {
            "likes_sent": likes_sent,
            "likes_received": likes_received,
            "skips": skips,
            "blocks": blocks,
            "questions_received": questions_received,
            "mutual_likes": mutual_likes,
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