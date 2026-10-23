"""Состояния aiogram (шаг анкеты, «пишу вопрос») в PostgreSQL.

Раньше жили в памяти и терялись при каждой пересборке на хостинге:
человек посреди анкеты начинал заново. Теперь переживают перезапуск.
"""

import json
from typing import Any, Mapping

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey

from database import get_pool


def _key(key: StorageKey) -> str:
    return ":".join(str(part) for part in (
        key.bot_id, key.chat_id, key.user_id, key.thread_id,
        key.business_connection_id, key.destiny,
    ))


class PgStorage(BaseStorage):
    async def set_state(self, key: StorageKey, state=None) -> None:
        value = state.state if isinstance(state, State) else state
        db = await get_pool()
        async with db.acquire() as conn:
            await conn.execute("""
                INSERT INTO fsm_states (key, state, updated_at) VALUES ($1, $2, now())
                ON CONFLICT (key) DO UPDATE SET state = $2, updated_at = now()
            """, _key(key), value)

    async def get_state(self, key: StorageKey) -> str | None:
        db = await get_pool()
        async with db.acquire() as conn:
            return await conn.fetchval("SELECT state FROM fsm_states WHERE key = $1", _key(key))

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        db = await get_pool()
        async with db.acquire() as conn:
            await conn.execute("""
                INSERT INTO fsm_states (key, data, updated_at) VALUES ($1, $2, now())
                ON CONFLICT (key) DO UPDATE SET data = $2, updated_at = now()
            """, _key(key), json.dumps(dict(data), ensure_ascii=False))

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        db = await get_pool()
        async with db.acquire() as conn:
            raw = await conn.fetchval("SELECT data FROM fsm_states WHERE key = $1", _key(key))
        return json.loads(raw) if raw else {}

    async def close(self) -> None:
        pass  # пул закрывает close_db()
