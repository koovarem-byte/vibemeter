import os
import aiosqlite


DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "vibemeter.db",
)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
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

        # Добавляем новые поля в уже существующую базу
        # Если они уже есть — просто пропускаем.
        try:
            await db.execute(
                "ALTER TABLE users ADD COLUMN gender TEXT"
            )
        except Exception:
            pass

        try:
            await db.execute(
                "ALTER TABLE users ADD COLUMN search_gender TEXT DEFAULT 'all'"
            )
        except Exception:
            pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user INTEGER NOT NULL,
                to_user INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user, to_user)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS skips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user INTEGER NOT NULL,
                to_user INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user, to_user)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user INTEGER NOT NULL,
                to_user INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user, to_user)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user INTEGER NOT NULL,
                to_user INTEGER NOT NULL,
                text TEXT NOT NULL,
                answer TEXT,
                answered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                answered_at TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_one INTEGER NOT NULL,
                user_two INTEGER NOT NULL,
                game_type TEXT NOT NULL DEFAULT 'vibe',
                question TEXT,
                answer_one TEXT,
                answer_two TEXT,
                status TEXT DEFAULT 'waiting',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                questions_json TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                question_index INTEGER NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(game_id, user_id, question_index)
            )
        """)

        await db.commit()

# =========================================================
# USERS
# =========================================================

async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )

        return await cursor.fetchone()


async def create_user(
    telegram_id: int,
    username: str | None = None,
    full_name: str | None = None,
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users (
                telegram_id,
                username,
                full_name
            )
            VALUES (?, ?, ?)
            """,
            (
                telegram_id,
                username,
                full_name,
            ),
        )

        await db.commit()


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
    fields = []
    values = []

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

    for field, value in data.items():
        if value is not None:
            fields.append(f"{field} = ?")
            values.append(value)

    if not fields:
        return

    values.append(telegram_id)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"""
            UPDATE users
            SET {", ".join(fields)}
            WHERE telegram_id = ?
            """,
            values,
        )

        await db.commit()
        
async def delete_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute(
            "DELETE FROM likes WHERE from_user = ? OR to_user = ?",
            (telegram_id, telegram_id),
        )

        await db.execute(
            "DELETE FROM skips WHERE from_user = ? OR to_user = ?",
            (telegram_id, telegram_id),
        )

        await db.execute(
            "DELETE FROM blocks WHERE from_user = ? OR to_user = ?",
            (telegram_id, telegram_id),
        )

        await db.execute(
            "DELETE FROM questions WHERE from_user = ? OR to_user = ?",
            (telegram_id, telegram_id),
        )

        await db.execute(
            "DELETE FROM game_answers WHERE user_id = ?",
            (telegram_id,),
        )

        await db.execute(
            """
            DELETE FROM games
            WHERE user_one = ?
            OR user_two = ?
            """,
            (telegram_id, telegram_id),
        )

        await db.execute(
            "DELETE FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )

        await db.commit()


# =========================================================
# LIKES
# =========================================================

async def add_like(from_user: int, to_user: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO likes (
                from_user,
                to_user
            )
            VALUES (?, ?)
            """,
            (from_user, to_user),
        )

        await db.commit()


async def has_like(from_user: int, to_user: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT 1
            FROM likes
            WHERE from_user = ?
            AND to_user = ?
            LIMIT 1
            """,
            (from_user, to_user),
        )

        return await cursor.fetchone() is not None


async def is_liked(from_user: int, to_user: int):
    return await has_like(from_user, to_user)


# =========================================================
# SKIPS
# =========================================================

async def add_skip(from_user: int, to_user: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO skips (
                from_user,
                to_user
            )
            VALUES (?, ?)
            """,
            (from_user, to_user),
        )

        await db.commit()


# =========================================================
# BLOCKS
# =========================================================

async def add_block(from_user: int, to_user: int):
    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute(
            """
            INSERT OR IGNORE INTO blocks (
                from_user,
                to_user
            )
            VALUES (?, ?)
            """,
            (from_user, to_user),
        )

        await db.execute(
            """
            DELETE FROM likes
            WHERE
                (from_user = ? AND to_user = ?)
                OR
                (from_user = ? AND to_user = ?)
            """,
            (
                from_user,
                to_user,
                to_user,
                from_user,
            ),
        )

        await db.commit()


async def is_blocked(from_user: int, to_user: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT 1
            FROM blocks
            WHERE from_user = ?
            AND to_user = ?
            LIMIT 1
            """,
            (from_user, to_user),
        )

        return await cursor.fetchone() is not None


# =========================================================
# CANDIDATES
# =========================================================

async def get_candidates(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT age, search_gender
            FROM users
            WHERE telegram_id = ?
            """,
            (user_id,),
        )

        current_user = await cursor.fetchone()

        if not current_user or current_user["age"] is None:
            return []

        if current_user["age"] < 18:
            age_condition = "u.age BETWEEN 16 AND 17"
        else:
            age_condition = "u.age >= 18"

        search_gender = current_user["search_gender"] or "all"

        gender_condition = ""

        if search_gender == "male":
            gender_condition = "AND u.gender = 'male'"
        elif search_gender == "female":
            gender_condition = "AND u.gender = 'female'"

        cursor = await db.execute(
            f"""
            SELECT u.*
            FROM users u

            WHERE u.telegram_id != ?

            AND u.age IS NOT NULL
            AND u.photo_id IS NOT NULL

            AND {age_condition}

            {gender_condition}

            AND NOT EXISTS (
                SELECT 1
                FROM likes l
                WHERE l.from_user = ?
                AND l.to_user = u.telegram_id
            )

            AND NOT EXISTS (
                SELECT 1
                FROM skips s
                WHERE s.from_user = ?
                AND s.to_user = u.telegram_id
            )

            AND NOT EXISTS (
                SELECT 1
                FROM blocks b
                WHERE
                    (b.from_user = ? AND b.to_user = u.telegram_id)
                    OR
                    (b.from_user = u.telegram_id AND b.to_user = ?)
            )

            ORDER BY RANDOM()
            """,
            (
                user_id,
                user_id,
                user_id,
                user_id,
                user_id,
            ),
        )

        return await cursor.fetchall()

# =========================================================
# INCOMING LIKES
# =========================================================

async def get_incoming_likes(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT u.*
            FROM users u

            INNER JOIN likes l
                ON l.from_user = u.telegram_id

            WHERE l.to_user = ?

            AND NOT EXISTS (
                SELECT 1
                FROM likes reverse_like
                WHERE
                    reverse_like.from_user = ?
                    AND reverse_like.to_user = u.telegram_id
            )

            AND NOT EXISTS (
                SELECT 1
                FROM blocks b
                WHERE
                    (b.from_user = ? AND b.to_user = u.telegram_id)
                    OR
                    (b.from_user = u.telegram_id AND b.to_user = ?)
            )

            ORDER BY l.created_at DESC
            """,
            (
                user_id,
                user_id,
                user_id,
                user_id,
            ),
        )

        return await cursor.fetchall()


# =========================================================
# QUESTIONS
# =========================================================

async def add_question(
    from_user: int,
    to_user: int,
    text: str,
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO questions (
                from_user,
                to_user,
                text
            )
            VALUES (?, ?, ?)
            """,
            (
                from_user,
                to_user,
                text,
            ),
        )

        await db.commit()

        return cursor.lastrowid


async def get_question(question_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT *
            FROM questions
            WHERE id = ?
            """,
            (question_id,),
        )

        return await cursor.fetchone()


async def answer_question(
    question_id: int,
    answer: str,
):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE questions
            SET
                answer = ?,
                answered = 1,
                answered_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                answer,
                question_id,
            ),
        )

        await db.commit()


async def get_pending_questions(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT *
            FROM questions
            WHERE to_user = ?
            AND answered = 0
            ORDER BY created_at DESC
            """,
            (user_id,),
        )

        return await cursor.fetchall()


# =========================================================
# GAMES
# =========================================================

async def create_game(
    user_one: int,
    user_two: int,
    questions_json: str,
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO games (
                user_one,
                user_two,
                game_type,
                question,
                questions_json,
                status
            )
            VALUES (?, ?, 'vibe', '', ?, 'waiting')
            """,
            (
                user_one,
                user_two,
                questions_json,
            ),
        )

        await db.commit()

        return cursor.lastrowid


async def get_game(game_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT *
            FROM games
            WHERE id = ?
            """,
            (game_id,),
        )

        return await cursor.fetchone()


async def add_game_answer(
    game_id: int,
    user_id: int,
    question_index: int,
    answer: str,
):
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                """
                INSERT INTO game_answers (
                    game_id,
                    user_id,
                    question_index,
                    answer
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    game_id,
                    user_id,
                    question_index,
                    answer,
                ),
            )

            await db.commit()

            return True

        except aiosqlite.IntegrityError:
            return False


async def get_game_answers(
    game_id: int,
    user_id: int,
):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT *
            FROM game_answers
            WHERE game_id = ?
            AND user_id = ?
            ORDER BY question_index
            """,
            (
                game_id,
                user_id,
            ),
        )

        return await cursor.fetchall()


async def finish_game(game_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE games
            SET status = 'finished'
            WHERE id = ?
            """,
            (game_id,),
        )

        await db.commit()


# =========================================================
# STATISTICS
# =========================================================

async def get_stats(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM likes
            WHERE from_user = ?
            """,
            (user_id,),
        )

        likes_sent = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM likes
            WHERE to_user = ?
            """,
            (user_id,),
        )

        likes_received = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM skips
            WHERE from_user = ?
            """,
            (user_id,),
        )

        skips = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM blocks
            WHERE from_user = ?
            """,
            (user_id,),
        )

        blocks = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM questions
            WHERE to_user = ?
            """,
            (user_id,),
        )

        questions_received = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM likes
            WHERE from_user = ?
            AND to_user IN (
                SELECT from_user
                FROM likes
                WHERE to_user = ?
            )
            """,
            (
                user_id,
                user_id,
            ),
        )

        mutual_likes = (await cursor.fetchone())[0]

        return {
            "likes_sent": likes_sent,
            "likes_received": likes_received,
            "skips": skips,
            "blocks": blocks,
            "questions_received": questions_received,
            "mutual_likes": mutual_likes,
        }

async def get_admin_stats():
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]

        cursor = await db.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE age IS NOT NULL
              AND city IS NOT NULL
              AND interests IS NOT NULL
              AND description IS NOT NULL
              AND photo_id IS NOT NULL
        """)
        profiles = (await cursor.fetchone())[0]

        cursor = await db.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE photo_id IS NOT NULL
        """)
        photos = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM likes")
        likes = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM skips")
        skips = (await cursor.fetchone())[0]

        cursor = await db.execute("""
            SELECT COUNT(*)
            FROM likes l1
            WHERE EXISTS (
                SELECT 1
                FROM likes l2
                WHERE l2.from_user = l1.to_user
                  AND l2.to_user = l1.from_user
            )
        """)
        mutual = (await cursor.fetchone())[0] // 2

        cursor = await db.execute("SELECT COUNT(*) FROM questions")
        questions = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM games")
        games = (await cursor.fetchone())[0]

        cursor = await db.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE DATE(created_at) = DATE('now')
        """)
        today = (await cursor.fetchone())[0]

        return {
            "total_users": total_users,
            "profiles": profiles,
            "photos": photos,
            "likes": likes,
            "mutual": mutual,
            "skips": skips,
            "questions": questions,
            "games": games,
            "today": today,
        }