"""Изолированная проверка привязки параметров SQL для app_game_start."""

import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import database


class FakeConnection:
    def __init__(self):
        self.advisory_args = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    def transaction(self):
        return self

    async def fetchval(self, query, *args):
        if "pg_advisory_xact_lock" in query:
            self.advisory_args = args
            return None
        if "SELECT EXISTS" in query:
            return False
        raise AssertionError(f"Unexpected query: {query}")

    async def execute(self, *_):
        return "UPDATE 0"

    async def fetchrow(self, *_):
        return {"id": 77, "rated": True}


class FakePool:
    def __init__(self, connection):
        self.connection = connection

    def acquire(self):
        return self.connection


class AppGameStartBindingTest(unittest.TestCase):
    def test_integer_telegram_id_is_bound_as_text_for_lock_key(self):
        conn = FakeConnection()
        old_get_pool = database.get_pool

        async def fake_get_pool():
            return FakePool(conn)

        async def run():
            database.get_pool = fake_get_pool
            try:
                game = await database.app_game_start(5171876077, "povyshenie")
            finally:
                database.get_pool = old_get_pool
            self.assertEqual(conn.advisory_args, ("5171876077", "povyshenie"))
            self.assertEqual(game["id"], 77)
            self.assertEqual(game["moves"], [])

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
