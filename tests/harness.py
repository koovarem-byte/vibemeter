"""Тестовый стенд (19.11): копия файлов как в Dockerfile, локальный PostgreSQL, поддельная сессия Telegram.

Нужен локальный PostgreSQL: пользователь postgres с паролем pg, база vibetest (стенд её пересоздаёт):
    service postgresql start && pip install -r requirements.txt
    su postgres -c "psql -c \"ALTER USER postgres PASSWORD 'pg';\""
    python3 tests/run.py
Токен и база ненастоящие, в Telegram ничего не уходит. В Docker не копируется.
"""
import asyncio, hashlib, hmac, json, os, shutil, sys, tempfile, time, glob, datetime, itertools
from urllib.parse import urlencode

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = "123456789:AAFakeTokenFakeTokenFakeTokenFakeTo1"
ADMIN = 1000

def prepare():
    d = tempfile.mkdtemp(prefix="vm_copy_")
    for f in glob.glob(f"{REPO}/*.py"):
        shutil.copy(f, d)
    for sub in ("webapp", "webapp_chess", "assets"):
        shutil.copytree(f"{REPO}/{sub}", f"{d}/{sub}")
    shutil.copy(f"{REPO}/situations.json", d)
    os.chdir(d); sys.path.insert(0, d)
    os.environ.update(BOT_TOKEN=TOKEN, ADMIN_ID=str(ADMIN),
                      DATABASE_URL="postgresql://postgres:pg@localhost/vibetest", BETA_SLOTS="30")
    os.environ.pop("ANTHROPIC_API_KEY", None)
    import asyncpg
    orig = asyncpg.create_pool
    def cp(*a, **k):
        k.pop("ssl", None); return orig(*a, **k)
    asyncpg.create_pool = cp
    return d

def reset_db():
    os.system("su postgres -c \"psql -q -c 'DROP DATABASE IF EXISTS vibetest' -c 'CREATE DATABASE vibetest'\" >/dev/null")

SENT = []
_mid = itertools.count(100)

def make_session():
    from aiogram.client.session.base import BaseSession
    from aiogram.types import Message, User, MessageId, Chat
    from aiogram.methods import GetMe
    class FakeSession(BaseSession):
        async def close(self): pass
        async def stream_content(self, *a, **k):
            if False: yield b""
        async def make_request(self, bot, method, timeout=None):
            SENT.append(method)
            ret = method.__returning__
            name = getattr(ret, "__name__", str(ret))
            if isinstance(method, GetMe):
                return User(id=123456789, is_bot=True, first_name="Шах и Чат", username="vibemeter_bot")
            if ret is Message or "Message" in str(ret) and "MessageId" not in str(ret) and "list" not in str(ret).lower():
                cid = getattr(method, "chat_id", None) or 1
                return Message(message_id=next(_mid), date=datetime.datetime.now(),
                               chat=Chat(id=int(cid) if str(cid).lstrip("-").isdigit() else 1, type="private"),
                               text=getattr(method, "text", None) or getattr(method, "caption", None) or "x")
            if ret is MessageId:
                return MessageId(message_id=next(_mid))
            if ret is bool or "bool" in str(ret):
                return True
            if "list" in str(ret).lower():
                return []
            if "StickerSet" in name:
                raise ConnectionError("no sticker set in tests")
            return True
    return FakeSession()

def texts(since=0):
    out = []
    for m in SENT[since:]:
        t = getattr(m, "text", None) or getattr(m, "caption", None)
        if t: out.append(t)
    return out

def buttons(m):
    rm = getattr(m, "reply_markup", None)
    if rm is None or not hasattr(rm, "inline_keyboard"): return []
    return [b for row in rm.inline_keyboard for b in row]

def last_buttons(since=0):
    for m in reversed(SENT[since:]):
        b = buttons(m)
        if b: return b
    return []

_uid = itertools.count(1)
def user_dict(uid, name="Тест"):
    return {"id": uid, "is_bot": False, "first_name": name, "username": f"u{uid}", "language_code": "ru"}

async def feed_msg(bot, dp, uid, text, name="Тест"):
    from aiogram.types import Update
    import ratelimit; ratelimit._hits.clear()
    n = len(SENT)
    upd = Update.model_validate({"update_id": next(_uid), "message": {
        "message_id": next(_mid), "date": int(time.time()), "chat": {"id": uid, "type": "private"},
        "from": user_dict(uid, name), "text": text,
        **({"entities": [{"type": "bot_command", "offset": 0, "length": len(text.split()[0])}]} if text.startswith("/") else {})}})
    await dp.feed_update(bot, upd)
    return n

async def feed_cb(bot, dp, uid, data, name="Тест"):
    from aiogram.types import Update
    import ratelimit; ratelimit._hits.clear()
    n = len(SENT)
    upd = Update.model_validate({"update_id": next(_uid), "callback_query": {
        "id": str(next(_uid)), "chat_instance": "ci", "data": data, "from": user_dict(uid, name),
        "message": {"message_id": next(_mid), "date": int(time.time()), "chat": {"id": uid, "type": "private"},
                    "from": {"id": 123456789, "is_bot": True, "first_name": "bot"}, "text": "x"}}})
    await dp.feed_update(bot, upd)
    return n

def init_data(uid, name="Тест"):
    user = json.dumps(user_dict(uid, name), separators=(",", ":"), ensure_ascii=False)
    fields = {"auth_date": str(int(time.time())), "query_id": "q1", "user": user}
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)

class Api:
    def __init__(self, client): self.c = client
    async def get(self, uid, path, expect=200):
        r = await self.c.get(path, headers={"X-Init-Data": init_data(uid)})
        body = await r.json() if r.content_type == "application/json" else await r.text()
        assert r.status == expect, (path, r.status, body)
        return body
    async def post(self, uid, path, data, expect=200):
        r = await self.c.post(path, json=data, headers={"X-Init-Data": init_data(uid)})
        body = await r.json() if r.content_type == "application/json" else await r.text()
        assert r.status == expect, (path, r.status, body)
        return body
