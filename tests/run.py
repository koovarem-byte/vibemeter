"""Полный прогон: init_db + create_app, команды бота через feed_update, все API Mini App, все партии до конца."""
import asyncio, logging, sys, random, os
sys.path.insert(0, os.path.dirname(__file__))
import harness as H
from harness import ADMIN

ERRORS = []
class Catch(logging.Handler):
    def emit(self, r):
        if r.levelno >= logging.ERROR and 'пак shahichat' not in r.getMessage() and 'Unclosed' not in r.getMessage(): ERRORS.append(self.format(r))

async def main():
    H.reset_db(); d = H.prepare(); print("копия:", d)
    logging.basicConfig(level=logging.WARNING); logging.getLogger().addHandler(Catch())
    import database, bot as botmod, partii, puzzles, chess_api
    from aiohttp.test_utils import TestServer, TestClient
    await database.init_db()
    await database.init_db()  # второй старт — как пересборка
    b, dp = botmod.create_bot_and_dispatcher()
    b.session = H.make_session()
    try:
        await botmod.load_emoji_pack(b)
    except Exception as e:
        print("emoji pack (ожидаемо без Telegram):", type(e).__name__)
    app = botmod.create_app(b, dp, webhook=False)
    client = TestClient(TestServer(app)); await client.start_server()
    api = H.Api(client)
    U = [2001, 2002, 2003]
    # ---- бот ----
    for uid in [ADMIN] + U:
        await H.feed_msg(b, dp, uid, "/start")
        await H.feed_cb(b, dp, uid, "consent:accept")
    for uid in U[:1] + [ADMIN]:
        for cmd in ["/help", "/me", "/top", "/fact", "/baza", "/daily"]:
            n0 = await H.feed_msg(b, dp, uid, cmd)
            assert len(H.SENT) > n0, ("нет ответа", cmd)
        await H.feed_msg(b, dp, uid, "привет, как прошёл день?")  # ответ на задачу дня
        await H.feed_msg(b, dp, uid, "/razbor"); await H.feed_msg(b, dp, uid, "/start")
        await H.feed_msg(b, dp, uid, "/ask"); await H.feed_msg(b, dp, uid, "как начать переписку?")
        await H.feed_msg(b, dp, uid, "/start play")
    # бот: все задачи по кнопкам
    uid = U[0]
    import keyboards
    n = await H.feed_msg(b, dp, uid, "/play")
    solved = 0
    for _ in range(len(puzzles.PUZZLES) + 2):
        btns = [x for x in H.last_buttons(n) if (x.callback_data or "").startswith("pz:")]
        if not btns: break
        n = await H.feed_cb(b, dp, uid, random.choice(btns).callback_data); solved += 1
        n = await H.feed_cb(b, dp, uid, "pz_next")
    print("бот: задач решено", solved, "(уровень start:", len(puzzles.pool("start")), ")")
    assert solved == len(puzzles.pool("start")) == 39, solved
    assert all(puzzles.PUZZLES[i]["level"] == "start" for i in puzzles.pool("start"))
    # /level в боте: переключаем на pro, задачи pro идут дальше
    n0 = await H.feed_msg(b, dp, uid, "/level"); assert "уровень" in H.texts(n0)[0]
    n0 = await H.feed_cb(b, dp, uid, "lvl:pro"); assert any("Опытный" in t for t in H.texts(n0)), H.texts(n0)
    n = await H.feed_msg(b, dp, uid, "/play"); more = 0
    for _ in range(30):
        btns = [x for x in H.last_buttons(n) if (x.callback_data or "").startswith("pz:")]
        if not btns: break
        n = await H.feed_cb(b, dp, uid, btns[0].callback_data); more += 1
        n = await H.feed_cb(b, dp, uid, "pz_next")
    assert more == 21, more
    print("бот: после /level pro ещё", more)
    import situations
    st_ = await situations.for_level("start"); pr_ = await situations.for_level("pro")
    assert all(s.get("level", "start") == "start" for s in st_) and len(pr_) > len(st_)
    assert (await situations.daily("start"))["level"] == "start"
    n0 = await H.feed_msg(b, dp, uid, "/help"); assert "/level" in H.texts(n0)[0]
    for cmd in ["/stats", "/admin", "/beta", "/beta_slots 40", "/beta_retest", "/beta_invite 1", "/beta_open 1",
                "/broadcast", "/sources", "/week", "/emojiset shahichat", "/reply 1 спасибо",
                "/add_situation test1 | привет | вы знакомы неделю | 1200 | Тест", "/chess_on", "/privacy", "/news"]:
        n0 = await H.feed_msg(b, dp, ADMIN, cmd)
        assert len(H.SENT) > n0, ("нет ответа", cmd)
    # ---- Mini App ----
    for uid in U:
        await api.get(uid, "/play/api/state")
        await api.post(uid, "/play/api/beta/join", {})
    for path in ["/play/api/state", "/play/api/top?period=day", "/play/api/top?period=week", "/play/api/top?period=all",
                 "/play/api/facts", "/play/api/profile", "/play/api/learn", "/play/api/partii"]:
        await api.get(U[1], path)
    lr = await api.get(U[1], "/play/api/learn")
    print("learn keys:", list(lr)[:6])
    # уровни в Mini App: по умолчанию start, партии и задачи по уровню
    st = await api.get(U[2], "/play/api/state")
    assert st["me"]["level"] == "start" and st["me"]["total"] == 39 and puzzles.PUZZLES[st["puzzle"]["id"]]["level"] == "start"
    pl = await api.get(U[2], "/play/api/partii")
    assert pl["level"] == "start" and {i["level"] for i in pl["items"]} == {"start"} and len(pl["items"]) == 6
    await api.post(U[2], "/play/api/level", {"level": "zzz"}, expect=400)
    lv = await api.post(U[2], "/play/api/level", {"level": "pro"})
    assert lv["me"]["level"] == "pro" and lv["me"]["total"] == 60 and puzzles.PUZZLES[lv["puzzle"]["id"]]["level"] == "pro" and lv["puzzle"]["daily"]
    pl = await api.get(U[2], "/play/api/partii")
    assert len(pl["items"]) == 12 and pl["items"][0]["level"] == "pro" and pl["items"][-1]["level"] == "start"
    await api.post(U[2], "/play/api/level", {"level": "start"})
    st = await api.get(U[2], "/play/api/state"); c2 = 0; pz = st["puzzle"]
    while pz:
        r = await api.post(U[2], "/play/api/move", {"id": pz["id"], "idx": pz["moves"][0]["idx"]}); c2 += 1; pz = r["puzzle"]
    assert c2 == 39 and r["me"]["solved"] == 39, (c2, r["me"])
    print("уровни в Mini App: ок")
    # все задачи в Mini App (опытный видит все 60)
    await api.post(U[1], "/play/api/level", {"level": "pro"})
    st = await api.get(U[1], "/play/api/state"); cnt = 0
    pz = st.get("puzzle")
    while pz:
        r = await api.post(U[1], "/play/api/move", {"id": pz["id"], "idx": random.choice(pz["moves"])["idx"]}); cnt += 1
        pz = r["puzzle"]
    print("Mini App: задач", cnt)
    assert cnt == len(puzzles.PUZZLES)
    await api.post(U[1], "/play/api/move", {"id": 0, "idx": 0}, expect=409)
    # все партии: лучший ход до конца, потом переигровка случайно; отзыв после 2
    uid = U[1]
    async def play(pid, pick):
        g = await api.post(uid, "/play/api/partiya/start", {"id": pid})
        stp = g["step"]; marks = []
        while True:
            idx = pick(pid, stp)
            r = await api.post(uid, "/play/api/partiya/move", {"game_id": g["game_id"], "idx": idx})
            marks.append(r["mark"])
            if "final" in r: return g, r["final"], marks
            stp = r["next"]
    def best(pid, stp):
        opts = partii.BY_ID[pid]["steps"][stp["n"] - 1]["options"]
        import rating
        return max((o["idx"] for o in stp["options"]), key=lambda i: rating.SCORE[opts[i][1]])
    def rnd(pid, stp): return random.choice(stp["options"])["idx"]
    fb = False
    for p in partii.PARTII:
        try:
            g, fin, marks = await play(p["id"], best)
        except AssertionError as e:
            if "need_feedback" in str(e) and not fb:
                await api.post(uid, "/play/api/feedback", {"stars": 5, "text": "норм игра, но мало задач"}); fb = True
                g, fin, marks = await play(p["id"], best)
            else: raise
        assert fin["result"] == "win", (p["id"], fin)
        g2, fin2, _ = await play(p["id"], rnd)
        assert not fin2["rated"]
        print(f"  {p['id']:12} {p['level']:5} лучшие: {fin['result']} {fin['before']}→{fin['after']} | случайно: {fin2['result']}")
    # пул: скрытый вариант нельзя сходить, переигровки показывают разные тройки
    import partii as PP
    g = await api.post(uid, "/play/api/partiya/start", {"id": "povyshenie"})
    vis = {o["idx"] for o in g["step"]["options"]}
    assert len(vis) == 3
    hidden = next(i for i in range(6) if i not in vis)
    await api.post(uid, "/play/api/partiya/move", {"game_id": g["game_id"], "idx": hidden}, expect=400)
    good = [o for o in g["step"]["options"] if PP.BY_ID["povyshenie"]["steps"][0]["options"][o["idx"]][1] in ("!!", "!")]
    assert good, g["step"]
    r = await api.post(uid, "/play/api/partiya/move", {"game_id": g["game_id"], "idx": good[0]["idx"]})
    assert len(r["others"]) == 2 and r["next"]["n"] == 2
    seen = set()
    for _ in range(6):
        g = await api.post(uid, "/play/api/partiya/start", {"id": "povyshenie"})
        seen.add(tuple(sorted(o["idx"] for o in g["step"]["options"])))
    print("разных троек за 6 переигровок:", len(seen)); assert len(seen) > 1
    # блиц: таймаут = ??, партия идёт дальше; без блица таймаут нельзя
    g = await api.post(uid, "/play/api/partiya/start", {"id": "gulyat", "blitz": True})
    assert g["blitz"] and g["seconds"] == 30
    r = await api.post(uid, "/play/api/partiya/move", {"game_id": g["game_id"], "timeout": True})
    assert r["mark"] == "??" and "next" in r and len(r["others"]) == 3 and r["best"], r
    for _ in range(3):
        r = await api.post(uid, "/play/api/partiya/move", {"game_id": g["game_id"], "timeout": True})
    assert r["final"]["result"] == "mate" and r["final"]["marks"] == ["??"] * 4, r["final"]
    g = await api.post(uid, "/play/api/partiya/start", {"id": "gulyat"})
    assert not g["blitz"]
    await api.post(uid, "/play/api/partiya/move", {"game_id": g["game_id"], "timeout": True}, expect=400)
    print("блиц: ок")
    pr = await api.get(uid, "/play/api/profile"); print("профиль:", pr["me"]["rating"], pr["me"]["rank"])
    # отзыв: невидимые и короткие
    for uid2 in [U[2]]:
        await api.post(uid2, "/play/api/feedback", {"stars": 3, "text": "abc"}, expect=400)
        for bad in ["\u200b" * 30, "\u3164" * 10, "\u2060 \u2060 \u2060 \u2060 \u2060 \u2060", "ок 👍👍👍👍👍", "\u200bа\u200bб\u200bв\u200b"]:
            await api.post(uid2, "/play/api/feedback", {"stars": 3, "text": bad}, expect=400)
        await api.post(uid2, "/play/api/feedback", {"stars": 4, "text": "  норм\u200b игра,\u2060 но мало задач  "})
        import database
        pool = await database.get_pool()
        t = await pool.fetchval("SELECT text FROM beta_feedback WHERE user_id = $1 ORDER BY id DESC LIMIT 1", uid2)
        assert t == "норм игра, но мало задач", repr(t)
        print("отзыв: невидимые символы режутся, пустой не проходит")
    await client.close()
    await b.session.close()
    print("ошибок в логе:", len(ERRORS))
    for e in ERRORS[:10]: print("ERR:", e[:800])
    return not ERRORS

if __name__ == "__main__":
    ok = asyncio.run(main())
    print("ИТОГ:", "OK" if ok else "ЕСТЬ ОШИБКИ"); sys.exit(0 if ok else 1)
