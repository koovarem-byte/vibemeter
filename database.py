import aiosqlite
import os

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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


async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )

        return await cursor.fetchone()


async def create_user(
        telegram_id: int,
        username: str = None,
        full_name: str = None
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
                full_name
            )
        )

        await db.commit()


async def update_user(
        telegram_id: int,
        username: str = None,
        full_name: str = None,
        age: int = None,
        city: str = None,
        interests: str = None,
        description: str = None,
        photo_id: str = None
):
    fields = []
    values = []

    if username is not None:
        fields.append("username = ?")
        values.append(username)

    if full_name is not None:
        fields.append("full_name = ?")
        values.append(full_name)

    if age is not None:
        fields.append("age = ?")
        values.append(age)

    if city is not None:
        fields.append("city = ?")
        values.append(city)

    if interests is not None:
        fields.append("interests = ?")
        values.append(interests)

    if description is not None:
        fields.append("description = ?")
        values.append(description)

    if photo_id is not None:
        fields.append("photo_id = ?")
        values.append(photo_id)

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
            values
        )

        await db.commit()


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
            (
                from_user,
                to_user
            )
        )

        await db.commit()


async def has_like(
    from_user: int,
    to_user: int,
):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT 1
            FROM likes
            WHERE from_user = ?
            AND to_user = ?
            """,
            (
                from_user,
                to_user,
            ),
        )

        return await cursor.fetchone() is not None

async def is_liked(from_user: int, to_user: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT 1
            FROM likes
            WHERE from_user = ?
            AND to_user = ?
            LIMIT 1
            """,
            (
                from_user,
                to_user
            )
        )

        return await cursor.fetchone() is not None


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
            (
                from_user,
                to_user
            )
        )

        await db.commit()


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
            (
                from_user,
                to_user
            )
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
                from_user
            )
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
            (
                from_user,
                to_user
            )
        )

        return await cursor.fetchone() is not None


async def get_candidates(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            """
            SELECT age
            FROM users
            WHERE telegram_id = ?
            """,
            (user_id,)
        )
    current_user = await cursor.fetchone()

    if not current_user or current_user["age"] is None:
        return []

    if current_user["age"] < 18:
        age_condition = "u.age BETWEEN 16 AND 17"
    else:
        age_condition = "u.age >= 18"

    cursor = await db.execute(
        f"""
                SELECT u.*
                FROM users u
                WHERE u.telegram_id != ?
                AND u.age IS NOT NULL
                AND {age_condition}

                AND NOT EXISTS (
                    SELECT 1
                    FROM likes l
                    WHERE
                        (l.from_user = ? AND l.to_user = u.telegram_id)
                        OR
                        (l.from_user = u.telegram_id AND l.to_user = ?)
                )

                AND NOT EXISTS (
                    SELECT 1
                    FROM skips s
                    WHERE
                        s.from_user = ?
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
            user_id
        )
    )

    return await cursor.fetchall()


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
                user_id
            )
        )

        return await cursor.fetchall()


async def add_question(
        from_user: int,
        to_user: int,
        text: str
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
                text
            )
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
            (question_id,)
        )

        return await cursor.fetchone()


async def answer_question(
        question_id: int,
        answer: str
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
                question_id
            )
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
            (user_id,)
        )

        return await cursor.fetchall()


async def create_game(
    user_one: int,
    user_two: int,
    questions_json: str
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
                questions_json
            )
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
            (game_id,)
        )

        return await cursor.fetchone()


async def add_game_answer(
    game_id: int,
    user_id: int,
    question_index: int,
    answer: str
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
                    answer
                )
            )

            await db.commit()

            return True

        except aiosqlite.IntegrityError:
            return False


async def get_game_answers(
    game_id: int,
    user_id: int
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
                user_id
            )
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
            (game_id,)
        )

        await db.commit()


async def get_stats(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM likes
            WHERE from_user = ?
            """,
            (user_id,)
        )

        likes_sent = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM likes
            WHERE to_user = ?
            """,
            (user_id,)
        )

        likes_received = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM skips
            WHERE from_user = ?
            """,
            (user_id,)
        )

        skips = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM blocks
            WHERE from_user = ?
            """,
            (user_id,)
        )

        blocks = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM questions
            WHERE to_user = ?
            """,
            (user_id,)
        )

        questions_received = (await cursor.fetchone())[0]

        return {
            "likes_sent": likes_sent,
            "likes_received": likes_received,
            "skips": skips,
            "blocks": blocks,
            "questions_received": questions_received
        }