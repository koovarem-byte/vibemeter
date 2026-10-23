"""Защита от спама: сколько действий можно за окно времени.

Счётчики в памяти: после перезапуска обнуляются, для защиты от
спамеров этого хватает. Админа не ограничиваем.
"""

import time
from collections import deque

# действие: (сколько, за сколько секунд)
LIMITS = {
    "flood": (25, 10),        # любые нажатия и сообщения
    "like": (100, 3600),      # вайбы: каждому приходит уведомление
    "question": (10, 3600),   # анонимные вопросы
}

_hits: dict[tuple[str, int], deque] = {}


def hit(action: str, user_id: int) -> bool:
    """Отмечает действие. False — лимит исчерпан, действие не делать."""
    limit, window = LIMITS[action]
    now = time.monotonic()
    queue = _hits.setdefault((action, user_id), deque())
    while queue and now - queue[0] > window:
        queue.popleft()
    if len(queue) >= limit:
        return False
    queue.append(now)
    return True
