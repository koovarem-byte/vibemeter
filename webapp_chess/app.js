/* Mini App «Шах и чат»: Игра · Топ · Факты · Профиль. Без сборки.
   Без Telegram (открыли в браузере) — демо-режим на моках. */
(() => {
  "use strict";

  const tg = window.Telegram && window.Telegram.WebApp;
  const initData = (tg && tg.initData) || "";
  const DEMO = !initData;
  const $ = (s, el = document) => el.querySelector(s);
  const screen = $("#screen");

  const MARKS = {
    "!!": { c: "var(--m-brill)", name: "Бриллиант" },
    "!": { c: "var(--m-good)", name: "Хороший ход" },
    "?!": { c: "var(--m-dub)", name: "Сомнительно" },
    "?": { c: "var(--m-mistake)", name: "Ошибка" },
    "??": { c: "var(--m-blunder)", name: "Зевок" },
    "#": { c: "var(--m-mate)", name: "Мат" },
  };
  const RANKS = [
    ["Пешка", "♟", 0], ["Конь", "♞", 100], ["Слон", "♝", 300],
    ["Ладья", "♜", 600], ["Ферзь", "♛", 1000], ["Гроссмейстер", "♚", 1500],
  ];
  const fig = (rank) => (RANKS.find((r) => r[0] === rank) || RANKS[0])[1];

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  let state = null; // ответ /state
  let tab = "game";
  let topPeriod = "all";

  if (tg) {
    tg.ready();
    tg.expand();
    try { tg.setHeaderColor("#0b0f0c"); tg.setBackgroundColor("#0b0f0c"); } catch (e) { /* старый клиент */ }
  }

  const haptic = (kind) => {
    try {
      if (kind === "tap") tg.HapticFeedback.selectionChanged();
      else tg.HapticFeedback.notificationOccurred(kind);
    } catch (e) { /* нет Telegram */ }
  };

  function toast(text) {
    const t = $("#toast");
    t.textContent = text;
    t.classList.remove("hidden");
    clearTimeout(toast.t);
    toast.t = setTimeout(() => t.classList.add("hidden"), 2200);
  }

  // ---------- API ----------
  async function api(path, body) {
    if (DEMO) return demo(path, body);
    const res = await fetch("/play/api/" + path, {
      method: body ? "POST" : "GET",
      headers: { "X-Init-Data": initData, "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.error || "http"), { code: data.error });
    return data;
  }

  // ---------- переписка ----------
  function chatHtml(text) {
    const m = /^([^:«]{1,24}):\s*«(.+)»\s*(.*)$/.exec(text);
    if (m) {
      return `<div class="who">${esc(m[1])}</div><div class="bubble">${esc(m[2])}</div>` +
        (m[3] ? `<div class="note">${esc(m[3])}</div>` : "");
    }
    return `<div class="situation">${esc(text)}</div>`;
  }

  function progress(me) {
    if (!me.next) return 100;
    return Math.max(3, Math.round(((me.rating - me.rank_from) / (me.next.at - me.rank_from)) * 100));
  }

  function headHtml(me) {
    const sub = me.next ? `${me.rating} · до «${me.next.rank}» ${me.next.at - me.rating}` : `${me.rating} · высшее звание`;
    return `
      <div class="head">
        <div class="rank-ico">${fig(me.rank)}</div>
        <div class="head-main">
          <div class="head-title">${esc(me.rank)}</div>
          <div class="head-sub" id="head-sub">${sub}</div>
          <div class="bar"><i id="bar" style="width:${progress(me)}%"></i></div>
        </div>
        ${me.streak > 0 ? `<div class="streak">🔥 ${me.streak}</div>` : ""}
      </div>`;
  }

  // ---------- Игра ----------
  function renderGame() {
    const { me, puzzle } = state;
    if (!puzzle) {
      screen.innerHTML = headHtml(me) + `
        <div class="empty"><div class="big">♚</div>
          <div class="h1">Все задачи решены</div>
          <p class="muted">Новые появляются каждую неделю. А пока — партия с ИИ в боте</p>
          <button class="btn" id="to-bot">Сыграть партию</button>
        </div>`;
      $("#to-bot").onclick = () => openBot("play");
      return;
    }
    screen.innerHTML = headHtml(me) + `
      <div class="task-label">
        <span class="pill">${puzzle.daily ? "♟ ЗАДАЧА ДНЯ" : "♟ ЗАДАЧА " + puzzle.number}</span>
        <span class="muted">${me.solved} из ${me.total}</span>
      </div>
      <div class="chat">${chatHtml(puzzle.chat)}</div>
      <div class="your-move">Твой ход</div>
      <div class="moves" id="moves">
        ${puzzle.moves.map((m) => `<button class="move" data-idx="${m.idx}">${esc(m.text)}</button>`).join("")}
      </div>`;
    $("#moves").onclick = (e) => {
      const b = e.target.closest(".move");
      if (b && !$("#moves").classList.contains("locked")) makeMove(puzzle, b);
    };
  }

  async function makeMove(puzzle, el) {
    haptic("tap");
    $("#moves").classList.add("locked");
    el.classList.add("picked");
    let res;
    try {
      res = await api("move", { id: puzzle.id, idx: +el.dataset.idx });
    } catch (e) {
      $("#moves").classList.remove("locked");
      el.classList.remove("picked");
      if (e.code === "already_solved") { toast("Эта задача уже решена"); return load(); }
      toast("Не получилось, попробуй ещё раз");
      return;
    }
    haptic(res.delta > 0 ? "success" : res.delta < 0 ? "error" : "warning");
    showVerdict(puzzle, el.textContent, res);
  }

  function showVerdict(puzzle, moveText, res) {
    const mk = MARKS[res.mark] || MARKS["?!"];
    const v = $("#verdict");
    const sign = res.delta > 0 ? "plus" : res.delta < 0 ? "minus" : "";
    v.innerHTML = `
      <div class="verdict-in" style="--c:${mk.c}">
        <div class="badge">${esc(res.mark)}</div>
        <div class="v-name">${esc(res.name)}</div>
        <div class="v-delta ${sign}">${res.delta > 0 ? "+" : ""}${res.delta} · рейтинг ${res.me.rating}</div>
        ${res.rank_up ? `<div class="rankup">${fig(res.me.rank)} Новое звание: ${esc(res.me.rank)}</div>` : ""}
        <div class="v-card"><div class="lbl">Почему</div>${esc(res.why)}</div>
        ${res.best ? `<div class="v-card"><div class="lbl">Лучший ход</div>«${esc(res.best)}»</div>` : ""}
        <button class="btn" id="v-next">${res.puzzle ? "Следующая задача" : "Готово"}</button>
        <div class="row">
          <button class="btn ghost" id="v-share">Скинуть другу</button>
          <button class="btn ghost" id="v-bot">Партия с ИИ</button>
        </div>
      </div>`;
    v.classList.remove("hidden");
    $("#v-next").onclick = () => {
      v.classList.add("hidden");
      state.me = res.me;
      state.puzzle = res.puzzle;
      renderGame();
    };
    $("#v-share").onclick = () => share(puzzle, res);
    $("#v-bot").onclick = () => openBot("play");
  }

  function share(puzzle, res) {
    const link = `https://t.me/${state.bot}?start=pz_${puzzle.id}`;
    const text = res.mark === "!!"
      ? `Я нашёл бриллиантовый ход ${res.mark} в «Шах и чат». А ты найдёшь?`
      : "Задача по переписке: какой ход лучший? Проверь себя";
    const url = `https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`;
    if (tg && tg.openTelegramLink) tg.openTelegramLink(url); else window.open(url, "_blank");
  }

  function openBot(cmd) {
    const url = `https://t.me/${state.bot}?start=${cmd}`;
    if (tg && tg.openTelegramLink) { tg.openTelegramLink(url); tg.close(); } else window.open(url, "_blank");
  }

  // ---------- Топ ----------
  async function renderTop() {
    screen.innerHTML = `<div class="h1">Топ игроков</div>
      <div class="seg" id="seg">
        <button data-p="day">Сегодня</button><button data-p="week">Неделя</button><button data-p="all">Всё время</button>
      </div><div id="top-body">${'<div class="skel"></div>'.repeat(4)}</div>`;
    [...$("#seg").children].forEach((b) => b.classList.toggle("active", b.dataset.p === topPeriod));
    $("#seg").onclick = (e) => {
      const b = e.target.closest("button");
      if (b && b.dataset.p !== topPeriod) { topPeriod = b.dataset.p; haptic("tap"); renderTop(); }
    };
    let data;
    try { data = await api("top?period=" + topPeriod); } catch (e) { $("#top-body").innerHTML = errorHtml(); return; }
    if (tab !== "top") return;
    const items = data.items;
    if (!items.length) {
      $("#top-body").innerHTML = `<div class="empty"><div class="big">♛</div><p class="muted">${topPeriod === "all" ? "Пока никто не играл" : "За этот период ещё никто не набрал очков"}. Стань первым</p></div>`;
      return;
    }
    const pts = (n) => (topPeriod === "all" ? n : (n > 0 ? "+" : "") + n);
    const pod = (it, cls) => it ? `
      <div class="pod ${cls}">
        ${cls === "p1" ? '<div class="crown">👑</div>' : ""}
        <div class="av">${esc(it.name[0] || "?")}</div>
        <div class="nm">${esc(it.name)}${it.me ? " (ты)" : ""}</div>
        <div class="pt">${pts(it.points)}</div>
        <div class="step">${it.place}</div>
      </div>` : "<div></div>";
    const rest = items.slice(3).map((it) => liHtml(it, pts)).join("");
    const mineVisible = items.some((it) => it.me);
    $("#top-body").innerHTML = `
      <div class="podium">${pod(items[1], "p2")}${pod(items[0], "p1")}${pod(items[2], "p3")}</div>
      <div class="list">${rest}</div>
      ${!mineVisible && data.me ? `<div class="me-pin">${liHtml({ ...data.me, name: "Ты", me: true, rank: state.me.rank }, pts)}</div>` : ""}
      ${!data.me ? `<p class="muted" style="text-align:center;margin-top:16px">Реши задачу — и ты в топе</p>` : ""}`;
  }

  const liHtml = (it, pts) => `
    <div class="li ${it.me ? "me" : ""}">
      <div class="pl">${it.place}</div>
      <div class="nm">${esc(it.name)}${it.me && it.name !== "Ты" ? " (ты)" : ""}</div>
      <div class="rk">${fig(it.rank)}</div>
      <div class="pt">${pts(it.points)}</div>
    </div>`;

  // ---------- Факты ----------
  async function renderFacts() {
    screen.innerHTML = `<div class="h1">Факты об общении</div>${'<div class="skel"></div>'.repeat(3)}`;
    let data;
    try { data = await api("facts"); } catch (e) { screen.innerHTML = errorHtml(); return; }
    if (tab !== "facts") return;
    const card = (f, day) => `
      <div class="fact ${day ? "day" : ""}">
        ${day ? '<span class="pill">✦ ФАКТ ДНЯ</span>' : ""}
        <div class="txt">${esc(f.text)}</div>
        <div class="tip"><span>💡</span><span>${esc(f.tip)}</span></div>
        <div class="src">${f.url ? `<a href="${esc(f.url)}" data-ext>${esc(f.source)}</a>` : esc(f.source)}</div>
      </div>`;
    screen.innerHTML = `<div class="h1">Факты об общении</div>${card(data.day, true)}
      <div class="h2">Ещё из исследований</div>${data.items.map((f) => card(f)).join("")}`;
  }

  // ---------- Профиль ----------
  async function renderProfile() {
    screen.innerHTML = `${'<div class="skel"></div>'.repeat(4)}`;
    let p;
    try { p = await api("profile"); } catch (e) { screen.innerHTML = errorHtml(); return; }
    if (tab !== "profile") return;
    const me = p.me;
    const order = ["!!", "!", "?!", "?", "??", "#"];
    const total = Object.values(p.marks).reduce((a, b) => a + b, 0);
    const maxN = Math.max(1, ...Object.values(p.marks));
    const marks = order.filter((k) => p.marks[k]).map((k) => `
      <div class="mk" style="--c:${MARKS[k].c}">
        <div class="b">${esc(k)}</div>
        <div class="tr"><i style="width:${Math.round((p.marks[k] / maxN) * 100)}%"></i></div>
        <div class="n">${p.marks[k]}</div>
      </div>`).join("");

    // очки по дням за 14 дней
    const byDay = Object.fromEntries(p.days.map((d) => [d.day, d.pts]));
    const days = [];
    const now = new Date(Date.now() + 3 * 3600e3); // Москва
    for (let i = 13; i >= 0; i--) {
      const d = new Date(now - i * 86400e3).toISOString().slice(0, 10);
      days.push([d, byDay[d] || 0]);
    }
    const maxAbs = Math.max(1, ...days.map((d) => Math.abs(d[1])));
    const chart = days.map(([d, v]) => `
      <div class="col" title="${d}: ${v}">
        <i class="${v < 0 ? "neg" : ""}" style="height:${Math.round((Math.abs(v) / maxAbs) * 78)}%"></i>
        <span>${+d.slice(8)}</span>
      </div>`).join("");

    const curIdx = RANKS.findIndex((r) => r[0] === me.rank);
    const ranks = RANKS.map((r, i) => `
      <div class="rk-step ${i <= curIdx ? "on" : ""} ${i === curIdx ? "cur" : ""}">
        <div class="f">${r[1]}</div><div class="l">${r[2]}</div>
      </div>`).join("");

    screen.innerHTML = `
      <div class="hero">
        <div class="rank-ico">${fig(me.rank)}</div>
        <div class="rt">${me.rating}</div>
        <div class="rn">${esc(me.rank)}</div>
        ${me.next ? `<div class="bar" style="max-width:240px;margin:10px auto 0"><i style="width:${progress(me)}%"></i></div>
          <div class="muted" style="font-size:13px;margin-top:6px">до «${esc(me.next.rank)}» ${me.next.at - me.rating}</div>` : ""}
      </div>
      <div class="stats">
        <div class="stat"><b>🔥 ${me.streak}</b><span>серия</span></div>
        <div class="stat"><b>${me.solved}/${me.total}</b><span>задач</span></div>
        <div class="stat"><b>${p.place || "—"}</b><span>место${p.players ? " из " + p.players : ""}</span></div>
      </div>
      <div class="h2">Звания</div><div class="ranks">${ranks}</div>
      <div class="h2">Очки за 2 недели</div><div class="chart">${chart}</div>
      <div class="h2">Мои ходы${total ? " · " + total : ""}</div>
      ${total ? `<div class="marks">${marks}</div>` : '<p class="muted">Реши первую задачу — тут появится, как ты ходишь</p>'}
      ${p.games ? `<div class="h2">Партии с ИИ</div><p>${p.games} сыграно · ${p.wins} побед</p>` : ""}`;
  }

  const errorHtml = () => `<div class="empty"><div class="big">♟</div><p class="muted">Не загрузилось. Проверь интернет</p>
    <button class="btn ghost" onclick="location.reload()">Обновить</button></div>`;

  // ---------- навигация ----------
  function go(name) {
    tab = name;
    [...$("#tabs").children].forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
    window.scrollTo(0, 0);
    if (name === "game") renderGame();
    else if (name === "top") renderTop();
    else if (name === "facts") renderFacts();
    else renderProfile();
  }

  $("#tabs").onclick = (e) => {
    const b = e.target.closest("button");
    if (b && b.dataset.tab !== tab) { haptic("tap"); go(b.dataset.tab); }
  };
  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[data-ext]");
    if (a && tg && tg.openLink) { e.preventDefault(); tg.openLink(a.href); }
  });

  async function load() {
    screen.innerHTML = '<div class="skel"></div>'.repeat(4);
    try {
      state = await api("state");
    } catch (e) {
      if (e.code === "no_user") {
        screen.innerHTML = `<div class="empty"><div class="big">♞</div><div class="h1">Сначала зайди в бота</div>
          <p class="muted">Нажми «Старт» в чате с ботом — и возвращайся сюда</p></div>`;
      } else if (e.code === "banned") {
        screen.innerHTML = `<div class="empty"><div class="big">♟</div><p class="muted">Доступ закрыт</p></div>`;
      } else {
        screen.innerHTML = errorHtml();
      }
      return;
    }
    const start = (location.hash || "").slice(1);
    go(["top", "facts", "profile"].includes(start) ? start : "game");
  }

  // ---------- демо без Telegram ----------
  const DEMO_P = [
    { id: 0, chat: "Она: «Меня повысили!!»", moves: [["Норм", "?!", "Сухо: человек делится радостью, а ты её гасишь"], ["Поздравляю!! Как это было? Отмечаем?", "!!", "Активная поддержка хороших новостей укрепляет отношения (Gable, 2004)"], ["Теперь будешь пропадать на работе", "??", "Обесценил радость — зевок"]] },
    { id: 1, chat: "Мэтч. Пустой чат. Твой первый ход", moves: [["Привет", "?!", "«Привет» получает ответ реже, чем сообщение по анкете"], ["Вижу, ты любишь горы — где было самое красивое место?", "!!", "Зацепка за анкету + открытый вопрос"], ["Ты очень красивая", "??", "Комплимент внешности первым сообщением работает хуже всего"]] },
  ];
  const D = { rating: 87, solved: 5, streak: 3 };
  const demoRank = (r) => [...RANKS].reverse().find((x) => r >= x[2]);
  function demoMe() {
    const rk = demoRank(D.rating);
    const nx = RANKS.find((x) => x[2] > D.rating);
    return { name: "Демо", rating: D.rating, rank: rk[0], rank_from: rk[2], next: nx ? { at: nx[2], rank: nx[0] } : null, streak: D.streak, solved: D.solved, total: 36 };
  }
  const demoPuzzle = (i) => i < DEMO_P.length ? { id: i, number: D.solved + 1, daily: i === 0, chat: DEMO_P[i].chat, moves: DEMO_P[i].moves.map((m, idx) => ({ idx, text: m[0] })) } : null;
  let demoI = 0;
  async function demo(path, body) {
    await new Promise((r) => setTimeout(r, 250));
    if (path === "state") return { me: demoMe(), puzzle: demoPuzzle(demoI), daily_done: false, bot: "vibemeter_bot" };
    if (path === "move") {
      const p = DEMO_P[body.id];
      const [, mark, why] = p.moves[body.idx];
      const delta = { "!!": 15, "!": 8, "?!": 0, "??": -5 }[mark];
      const before = demoMe().rank;
      D.rating = Math.max(0, D.rating + delta); D.solved++; demoI++;
      const best = p.moves.find((m) => m[1] === "!!");
      return { mark, name: MARKS[mark].name, why, best: best[1] !== mark ? best[0] : null, delta, rank_up: demoMe().rank !== before, me: demoMe(), puzzle: demoPuzzle(demoI) };
    }
    if (path.startsWith("top")) {
      const names = ["Артём", "Лиза", "Макс", "Даня", "Соня", "Егор", "Вика"];
      const items = names.map((n, i) => ({ place: i + 1, name: n, points: 420 - i * 47, rank: demoRank(420 - i * 47)[0], me: false }));
      return { items, me: { place: 14, points: D.rating, total: 120 } };
    }
    if (path === "facts") {
      const f = (t, tip, s) => ({ id: t, text: t, tip, source: s, url: null });
      return { day: f("Кто задаёт больше уточняющих вопросов, тот нравится собеседнику сильнее", "Спроси «а почему?» после ответа", "Huang и др., 2017"),
        items: [f("После разговора люди недооценивают, насколько понравились собеседнику", "Скорее всего, ты понравился больше, чем думаешь", "Boothby и др., 2018")] };
    }
    if (path === "profile") {
      const today = new Date(Date.now() + 3 * 3600e3);
      const days = [0, 1, 3, 4, 7].map((i, k) => ({ day: new Date(today - i * 86400e3).toISOString().slice(0, 10), pts: [23, 15, -5, 30, 8][k] }));
      return { me: demoMe(), marks: { "!!": 3, "!": 4, "?!": 2, "??": 1 }, days, games: 2, wins: 1, solved_today: 1, place: 14, players: 120 };
    }
    return {};
  }

  load();
})();
