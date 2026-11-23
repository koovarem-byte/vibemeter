"""Изолированные проверки публичного запуска без подключения к PostgreSQL."""
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chess_api
import database


class FakeContext:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *_):
        return False


class FakeConnection:
    def __init__(self):
        self.state = {}
        self.rating_updates = 0

    def transaction(self):
        return FakeContext(self)

    async def execute(self, query, *args):
        if "UPDATE users SET chess_rating = 0" in query:
            self.rating_updates += 1
        if "INSERT INTO app_state" in query and args:
            if "public_rating_reset_at" in query:
                self.state["public_rating_reset_at"] = args[0]
            elif "public_feedback_since" in query:
                self.state["public_feedback_since"] = args[0]
            else:
                self.state[args[0]] = args[1]

    async def fetchval(self, query, *args):
        if "SELECT 1 FROM app_state" in query:
            return 1 if "public_rating_reset_at" in self.state else None
        if "SELECT now()" in query:
            return datetime(2026, 11, 23, tzinfo=timezone.utc)
        raise AssertionError(f"Unexpected query: {query}")


class FakePool:
    def __init__(self):
        self.connection = FakeConnection()

    def acquire(self):
        return FakeContext(self.connection)


class PublicReleaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_feedback_required_at_15_tasks(self):
        self.assertEqual(chess_api.BETA_SLOTS, 0)
        with patch.object(database, "feedback_task_count", new=AsyncMock(return_value=14)):
            self.assertFalse(await chess_api.need_feedback(424242))
        with patch.object(database, "feedback_task_count", new=AsyncMock(return_value=15)):
            self.assertTrue(await chess_api.need_feedback(424242))
            self.assertFalse(await chess_api.need_feedback(chess_api.ADMIN_ID))

    async def test_rating_reset_is_idempotent(self):
        pool = FakePool()
        with patch.object(database, "get_pool", new=AsyncMock(return_value=pool)):
            self.assertTrue(await database.reset_public_ratings_once())
            self.assertFalse(await database.reset_public_ratings_once())
        self.assertEqual(pool.connection.rating_updates, 1)
        self.assertIn("public_rating_reset_at", pool.connection.state)
        self.assertIn("public_feedback_since", pool.connection.state)


if __name__ == "__main__":
    unittest.main()
