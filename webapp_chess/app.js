/* Mini App «Шах и Чат»: Главная · Задачи · Рейтинг · Профиль (+ Обучение и Достижения). Без сборки.
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
    "!?": { c: "#8fd14f", name: "Интересный ход" },
    "?": { c: "var(--m-mistake)", name: "Ошибка" },
    "??": { c: "var(--m-blunder)", name: "Зевок" },
    "#": { c: "var(--m-mate)", name: "Мат" },
  };
  // залитые фигуры + U+FE0E: текстовый глиф, не эмодзи (белые 2D-силуэты как конь на логотипе)
  const T = "︎";
  const RANKS = [
    ["Пешка", "♟" + T, 0], ["Конь", "♞" + T, 200], ["Слон", "♝" + T, 400],
    ["Ладья", "♜" + T, 700], ["Ферзь", "♛" + T, 1000], ["Гроссмейстер", "♚" + T, 1400],
  ];
  const PIECE_IMG = { "Пешка": "pawn", "Конь": "knight", "Слон": "bishop", "Ладья": "rook", "Ферзь": "queen", "Гроссмейстер": "king" };
  const MARK_IMG = { "!!": "m_brilliant", "!": "m_good", "?!": "m_dubious", "??": "m_blunder", "#": "m_mate" };
  const icon = (name, cls = "ic") => `<img class="${cls}" src="i/${name}.png" alt="">`;
  const piece = (rank) => icon(PIECE_IMG[rank] || "pawn", "ic piece-img");
  const LOGO = "logo.png";

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  let state = null; // ответ /state
  let profile = null; // ответ /profile (кешируем для достижений)
  let tab = "home";
  let topPeriod = "all";

  if (tg) {
    tg.ready();
    tg.expand();
    try { tg.setHeaderColor("#06120a"); tg.setBackgroundColor("#06120a"); } catch (e) { /* старый клиент */ }
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

  function openTg(url) {
    if (tg && tg.openTelegramLink) tg.openTelegramLink(url); else window.open(url, "_blank");
  }
  function openBot(cmd) {
    openTg(`https://t.me/${state.bot}?start=${cmd}`);
    if (tg) setTimeout(() => tg.close(), 300);
  }
  function shareLink(start, text) {
    const link = `https://t.me/${state.bot}?start=${start}`;
    openTg(`https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`);
  }

  // ---------- общие куски ----------
  function progress(me) {
    if (!me.next) return 100;
    return Math.max(3, Math.round(((me.rating - me.rank_from) / (me.next.at - me.rank_from)) * 100));
  }

  function chatHtml(text) {
    const m = /^([^:«]{1,24}):\s*«(.+)»\s*(.*)$/.exec(text);
    if (m) {
      return `<div class="who">${esc(m[1])}</div><div class="bubble">${esc(m[2])}</div>` +
        (m[3] ? `<div class="note">${esc(m[3])}</div>` : "");
    }
    return `<div class="situation">${esc(text)}</div>`;
  }

  const hue = (s) => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) % 360, 7);

  // ---------- Главная ----------
  // уровень (19.11): «Начинаю» — школа и первые переписки, «Опытный» — отношения
  const LEVELS = [["start", "Начинаю"], ["pro", "Опытный"]];
  function levelHtml(level) {
    return `<div class="seg" id="level-seg">${LEVELS.map(([k, t]) => {
      const active = (level || "start") === k;
      return `<button class="${active ? "on" : ""}" aria-pressed="${active}" data-level="${k}">${t}</button>`;
    }).join("")}</div>`;
  }
  async function setLevel(level) {
    if ((state.me.level || "start") === level) return;
    haptic("tap");
    let res;
    try { res = await api("level", { level }); } catch (e) { toast("Не получилось, попробуй ещё раз"); return; }
    Object.assign(state, res);
    toast(level === "pro" ? "Опытный: отношения, бывшие, ссоры" : "Начинаю: школа, друзья, первые переписки");
    if (tab === "partii") renderPartii(); else if (tab === "home") renderHome(); else if (tab === "game") renderGame();
  }

  function renderHome() {
    const { me } = state;
    const daily = state.daily_done
      ? `<button class="card done" data-go="game"><div class="ico">${icon("check")}</div><div class="main"><div class="t">Задача дня решена</div><div class="s">Дальше — обычные задачи</div></div><div class="arrow">›</div></button>`
      : `<button class="card" data-go="game"><div class="ico">${icon("daily")}</div><div class="main"><div class="t">Задача дня ждёт</div><div class="s">Одна на всех · серия ${me.streak}</div></div><div class="arrow">›</div></button>`;
    screen.innerHTML = `
      <div class="hero">
        <img src="${LOGO}" alt="">
        <div class="brand">Шах и <span>Чат</span></div>
        <div class="tagline">Общайся. Учись. Побеждай.</div>
      </div>
      ${levelHtml(me.level)}
      <button class="btn big" data-go="partii">Начать партию ▶</button>
      <button class="card" data-go="top">
        <div class="ico">${icon("rating")}</div>
        <div class="main"><div class="t">Твой рейтинг: ${me.rating}</div><div class="s">${esc(me.rank)}${me.next ? ` · до «${esc(me.next.rank)}» ${me.next.at - me.rating}` : ""}</div>
          <div class="bar"><i style="width:${progress(me)}%"></i></div></div>
        <div class="arrow">›</div>
      </button>
      ${daily}
      <div class="tiles">
        <button class="tile" data-go="learn">${icon("chat", "ti")}Обучение</button>
        <button class="tile" data-go="ach">${icon("star", "ti")}Достижения</button>
        <button class="tile" data-feedback>${icon("bell", "ti")}Отзыв</button>
        <button class="tile" data-invite>${icon("gift", "ti")}Позвать друга</button>
      </div>`;
  }

  // ---------- Задачи ----------
  function headHtml(me) {
    const sub = me.next ? `${me.rating} · до «${me.next.rank}» ${me.next.at - me.rating}` : `${me.rating} · высшее звание`;
    return `
      <div class="head">
        <div class="rank-ico">${piece(me.rank)}</div>
        <div class="head-main">
          <div class="head-title">${esc(me.rank)}</div>
          <div class="head-sub">${sub}</div>
          <div class="bar"><i style="width:${progress(me)}%"></i></div>
        </div>
        ${me.streak > 0 ? `<div class="streak">${icon("fire")} ${me.streak}</div>` : ""}
      </div>`;
  }

  function renderGame() {
    const { me, puzzle } = state;
    if (!puzzle) {
      screen.innerHTML = headHtml(me) + `
        <div class="empty"><img src="${LOGO}" alt="">
          <div class="title">Все задачи решены</div>
          <p class="muted">Новые появляются каждую неделю. А пока — партия с ИИ в боте</p>
          <button class="btn" data-bot="play">Сыграть партию</button>
        </div>`;
      return;
    }
    screen.innerHTML = headHtml(me) + `
      <div class="task-label">
        <span class="pill">${puzzle.daily ? "ЗАДАЧА ДНЯ" : "ЗАДАЧА " + puzzle.number}</span>
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
      if (e.code === "need_feedback") { state.beta.need_feedback = true; return openFeedback(true); }
      $("#moves").classList.remove("locked");
      el.classList.remove("picked");
      if (e.code === "already_solved") { toast("Эта задача уже решена"); return load(); }
      toast("Не получилось, попробуй ещё раз");
      return;
    }
    haptic(res.delta > 0 ? "success" : res.delta < 0 ? "error" : "warning");
    profile = null;
    if (puzzle.daily) state.daily_done = true;
    if (res.rated === false) toast("Переигровка после обновления, без рейтинга");
    showVerdict(puzzle, res);
    if (res.need_feedback) openFeedback(true);
  }

  function showVerdict(puzzle, res) {
    const mk = MARKS[res.mark] || MARKS["?!"];
    const v = $("#verdict");
    const sign = res.delta > 0 ? "plus" : res.delta < 0 ? "minus" : "";
    v.innerHTML = `
      <div class="verdict-in" style="--c:${mk.c}">
        ${MARK_IMG[res.mark] ? icon(MARK_IMG[res.mark], "badge-img") : `<div class="badge">${esc(res.mark)}</div>`}
        <div class="v-name">${esc(res.name)}</div>
        <div class="v-delta ${sign}">${res.delta > 0 ? "+" : ""}${res.delta} · рейтинг ${res.me.rating}</div>
        ${res.rank_up ? `<div class="rankup">${piece(res.me.rank)} Новое звание: ${esc(res.me.rank)}</div>` : ""}
        <div class="v-card"><div class="lbl">Почему</div>${esc(res.why)}</div>
        ${res.best ? `<div class="v-card"><div class="lbl">Лучший ход</div>«${esc(res.best)}»</div>` : ""}
        ${othersHtml(res.others)}
        <button class="btn" id="v-next">${res.puzzle ? "Следующая задача" : "Готово"}</button>
        <div class="row">
          <button class="btn ghost" id="v-share">Скинуть другу</button>
          <button class="btn ghost" data-go="partii">К партиям</button>
        </div>
      </div>`;
    v.classList.remove("hidden");
    $("#v-next").onclick = () => {
      v.classList.add("hidden");
      state.me = res.me;
      state.puzzle = res.puzzle;
      renderGame();
    };
    $("#v-share").onclick = () => shareLink(`pz_${puzzle.id}`, res.mark === "!!"
      ? "Я нашёл бриллиантовый ход !! в «Шах и Чат». А ты найдёшь?"
      : "Задача по переписке: какой ход лучший? Проверь себя");
  }

  // ---------- Рейтинг ----------
  async function renderTop() {
    screen.innerHTML = `<div class="title">Рейтинг</div><p class="subtitle">Кто лучше всех ведёт переписку</p>
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
    const pts = (n) => (topPeriod === "all" ? n : (n > 0 ? "+" : "") + n);
    if (!data.items.length && !data.owner) {
      $("#top-body").innerHTML = `<div class="empty"><img src="${LOGO}" alt=""><p class="muted">${topPeriod === "all" ? "Пока никто не играл" : "За этот период ещё никто не набрал очков"}. Стань первым</p></div>`;
      return;
    }
    const mineVisible = data.items.some((it) => it.me);
    const ownerRow = data.owner ? `<div class="li owner">${icon("crown_gold", "ic")}<div class="nm"><b>${esc(data.owner.name)}${data.owner.me ? " (ты)" : ""}</b><span>Автор игры · вне рейтинга</span></div><div class="pt">${data.owner.points}</div></div>` : "";
    $("#top-body").innerHTML = ownerRow + `
      <div class="list">${data.items.map((it) => liHtml(it, pts)).join("")}</div>
      ${!mineVisible && data.me ? `<div class="me-pin">${liHtml({ ...data.me, name: "Ты", me: true, rank: state.me.rank }, pts)}</div>` : ""}
      ${!data.me ? `<p class="muted" style="text-align:center;margin-top:16px">Реши задачу — и ты в рейтинге</p>` : ""}`;
  }

  function liHtml(it, pts) {
    const cls = it.place <= 3 ? ` m${it.place}` : "";
    const av = it.me
      ? `<div class="av knight"><img src="${LOGO}" alt=""></div>`
      : `<div class="av ${it.place === 1 ? "top1" : ""}" style="--h:${hue(it.name)}">${esc((it.name || "?")[0].toUpperCase())}</div>`;
    return `
      <div class="li ${it.me ? "me" : ""}">
        <div class="pl${cls}">${it.place <= 3 && !it.me ? icon("crown", "ic pl-crown") : ""}${it.place}</div>${av}
        <div class="nm"><b>${it.me ? "Ты" : esc(it.name)}</b><span>${esc(it.rank)}</span></div>
        <div class="pt">${pts(it.points)}</div>
      </div>`;
  }

  // ---------- Обучение: 3 статьи в день, проверка после каждой (18.11) ----------
  let learnData = null;
  const LEARN_HEAD = `<button class="back" data-go="home">‹ Главная</button><div class="title">Обучение</div>`;
  const learnSub = (d) => `<p class="subtitle">${d.per_day} статьи в день · верный ответ +${d.reward} очка знаний</p>
    <div class="fact" style="display:flex;justify-content:space-between;align-items:center"><span>${icon("star")} Очки знаний</span><b style="font-size:22px">${d.points || 0}</b></div>`;

  async function renderLearn() {
    screen.innerHTML = `${LEARN_HEAD}${'<div class="skel"></div>'.repeat(3)}`;
    try { learnData = await api("learn"); } catch (e) { screen.innerHTML = errorHtml(); return; }
    if (tab !== "learn") return;
    learnList();
  }

  function learnList() {
    const d = learnData;
    const status = (it) => it.answered
      ? (it.ok ? `<span class="pill">${it.earned ? "+" + d.reward : "верно"}</span>` : `<span class="pill no">мимо</span>`)
      : `<div class="arrow">›</div>`;
    const card = (it, i) => `
      <button class="card ${it.answered ? "done" : ""}" data-art="${esc(it.id)}">
        <div class="ico">${icon(it.answered ? (it.ok ? "check" : "cross") : "chat")}</div>
        <div class="main"><div class="t">Статья ${i + 1}</div><div class="s">${esc(it.text.slice(0, 70))}…</div></div>
        ${status(it)}
      </button>`;
    const all = d.done >= d.items.length;
    screen.innerHTML = `${LEARN_HEAD}${learnSub(d)}
      <div class="h2">Сегодня <small>${d.done} из ${d.items.length}</small></div>
      <div id="l-list">${d.items.map(card).join("")}</div>
      ${all ? `<div class="fact day"><span class="pill">НА СЕГОДНЯ ВСЁ</span><div class="txt">Новые статьи завтра. А пока сыграй партию</div></div>
               <button class="btn" data-go="partii">К партиям</button>` : ""}
      <p class="muted" style="margin-top:14px">Прочитано всего: ${d.total_read} из ${d.all}</p>`;
    $("#l-list").onclick = (e) => {
      const b = e.target.closest("[data-art]");
      if (b) { haptic("tap"); learnArticle(b.dataset.art); }
    };
  }

  function learnArticle(id) {
    const it = learnData.items.find((x) => x.id === id);
    if (!it) return learnList();
    if (!it.opened) { it.opened = true; api("learn/open", { id }).catch(() => {}); }
    screen.innerHTML = `<button class="back" id="l-back">‹ Обучение</button>
      <div class="fact day">
        <span class="pill">СТАТЬЯ ${learnData.items.indexOf(it) + 1} ИЗ ${learnData.items.length}</span>
        <div class="txt">${esc(it.text)}</div>
        <div class="tip">${icon("target")}<span>${esc(it.tip)}</span></div>
        <div class="src">${it.url ? `<a href="${esc(it.url)}" data-ext>${esc(it.source)}</a>` : esc(it.source)}</div>
      </div>
      ${it.answered ? learnResultHtml(it) : `<button class="btn big" id="l-quiz">Прочитал, проверь меня</button>`}`;
    $("#l-back").onclick = () => learnList();
    const q = $("#l-quiz");
    if (q) q.onclick = () => learnQuiz(it);
    learnNextBtn(it);
  }

  function learnQuiz(it) {
    haptic("tap");
    screen.innerHTML = `<button class="back" id="l-back">‹ К статье</button>
      <div class="title">Проверка</div>
      <p class="subtitle">${esc(it.question)}</p>
      <div class="moves" id="l-opts">${it.options.map((o) => `<button class="move" data-idx="${o.idx}">${esc(o.text)}</button>`).join("")}</div>
      <p class="muted" style="margin-top:12px">Одна попытка${it.reward ? ` · верно — +${it.reward} очка знаний` : ""}</p>`;
    $("#l-back").onclick = () => learnArticle(it.id);
    $("#l-opts").onclick = async (e) => {
      const b = e.target.closest("[data-idx]");
      if (!b || $("#l-opts").classList.contains("locked")) return;
      $("#l-opts").classList.add("locked");
      b.classList.add("picked");
      let r;
      try { r = await api("learn/quiz", { id: it.id, idx: +b.dataset.idx }); }
      catch (err) {
        if (err.code === "need_feedback") { state.beta.need_feedback = true; return openFeedback(true); }
        $("#l-opts").classList.remove("locked"); return toast("Не получилось, попробуй ещё раз");
      }
      haptic(r.ok ? "success" : "error");
      if (r.me) state.me = r.me;
      learnData = r.learn;
      const fresh = learnData.items.find((x) => x.id === it.id) || Object.assign(it, { answered: true, ok: r.ok, correct: r.correct });
      fresh.delta = r.delta;
      screen.innerHTML = `<button class="back" id="l-back">‹ Обучение</button>${learnResultHtml(fresh)}`;
      $("#l-back").onclick = () => learnList();
      learnNextBtn(fresh);
      if (r.need_feedback) openFeedback(true);
    };
  }

  function learnResultHtml(it) {
    return `<div class="fact ${it.ok ? "day" : ""}">
        <span class="pill ${it.ok ? "" : "no"}">${it.ok ? "ВЕРНО" : "МИМО"}</span>
        <div class="txt">${it.ok ? (it.delta ? `+${it.delta} очка знаний` : "Так и есть") : "Правильный ответ: " + esc(it.correct || "")}</div>
        <div class="src">${esc(it.question)}</div>
      </div><div id="l-next"></div>`;
  }

  function learnNextBtn(it) {
    const box = $("#l-next");
    if (!box) return;
    const next = learnData.items.find((x) => !x.answered && x.id !== it.id);
    box.innerHTML = next
      ? `<button class="btn big" id="l-go">Следующая статья</button>`
      : `<button class="btn big" id="l-go">Готово на сегодня</button>`;
    $("#l-go").onclick = () => (next ? learnArticle(next.id) : learnList());
  }

  // ---------- Достижения ----------
  function achievements(p) {
    const me = p.me;
    const m = p.marks;
    return [
      ["pawn", "Первый ход", "Реши первую задачу", me.solved >= 1],
      ["m_brilliant", "Бриллиант", "Найди ход !!", (m["!!"] || 0) >= 1],
      ["crown", "Ювелир", "10 ходов !!", (m["!!"] || 0) >= 10],
      ["target", "Десятка", "Реши 10 задач", me.solved >= 10],
      ["fire", "Три дня", "Играй 3 дня подряд", me.best_streak >= 3],
      ["fire_x5", "Неделя", "Играй 7 дней подряд", me.best_streak >= 7],
      ["chat", "Первая партия", "Доиграй партию", p.games >= 1],
      ["trophy", "Первая победа", "Выиграй партию", p.wins >= 1],
      ["knight_gold", "Стратег", "Выиграй 5 партий", p.wins >= 5],
      ["knight", "Конь", "Рейтинг 200", me.rating >= 200],
      ["rook", "Ладья", "Рейтинг 700", me.rating >= 700],
      ["king", "Гроссмейстер", "Рейтинг 1400", me.rating >= 1400],
    ];
  }
  const medal = (name) => icon(name);

  async function loadProfile() {
    if (!profile) profile = await api("profile");
    return profile;
  }

  async function renderAch() {
    screen.innerHTML = `<button class="back" data-go="home">‹ Главная</button><div class="title">Достижения</div>${'<div class="skel"></div>'.repeat(4)}`;
    let p;
    try { p = await loadProfile(); } catch (e) { screen.innerHTML = errorHtml(); return; }
    if (tab !== "ach") return;
    const list = achievements(p);
    const done = list.filter((a) => a[3]).length;
    screen.innerHTML = `<button class="back" data-go="home">‹ Главная</button>
      <div class="title">Достижения</div><p class="subtitle">Открыто ${done} из ${list.length}</p>
      <div class="ach-list">${list.map(([ico, name, hint, ok]) => `
        <div class="card ${ok ? "" : "locked"}"><div class="ico">${medal(ico)}</div>
          <div class="main"><div class="t">${esc(name)}</div><div class="s">${esc(hint)}</div></div>
          ${ok ? icon("check", "ic check-img") : ""}
        </div>`).join("")}</div>`;
  }

  // ---------- Профиль ----------
  async function renderProfile() {
    screen.innerHTML = '<div class="skel"></div>'.repeat(4);
    let p;
    try { p = await loadProfile(); } catch (e) { screen.innerHTML = errorHtml(); return; }
    if (tab !== "profile") return;
    const me = p.me;
    const order = ["!!", "!", "?!", "?", "??", "#"];
    const total = Object.values(p.marks).reduce((a, b) => a + b, 0);
    const maxN = Math.max(1, ...Object.values(p.marks));
    const marks = order.filter((k) => p.marks[k]).map((k) => `
      <div class="mk" style="--c:${MARKS[k].c}">
        ${MARK_IMG[k] ? icon(MARK_IMG[k], "ic mk-img") : `<div class="b">${esc(k)}</div>`}
        <div class="tr"><i style="width:${Math.round((p.marks[k] / maxN) * 100)}%"></i></div>
        <div class="n">${p.marks[k]}</div>
      </div>`).join("");

    // очки по дням за 14 дней (Москва)
    const byDay = Object.fromEntries(p.days.map((d) => [d.day, d.pts]));
    const now = Date.now() + 3 * 3600e3;
    const days = [];
    for (let i = 13; i >= 0; i--) {
      const d = new Date(now - i * 86400e3).toISOString().slice(0, 10);
      days.push([d, byDay[d] || 0]);
    }
    const maxAbs = Math.max(1, ...days.map((d) => Math.abs(d[1])));
    const chart = days.map(([d, v]) => `
      <div class="col"><i class="${v < 0 ? "neg" : ""}" style="height:${Math.round((Math.abs(v) / maxAbs) * 78)}%"></i><span>${+d.slice(8)}</span></div>`).join("");

    const curIdx = RANKS.findIndex((r) => r[0] === me.rank);
    const ranks = RANKS.map((r, i) => `
      <div class="rk-step ${i <= curIdx ? "on" : ""} ${i === curIdx ? "cur" : ""}">${piece(r[0])}<div class="l">${r[2]}</div></div>`).join("");

    const ach = achievements(p);
    const achDone = ach.filter((a) => a[3]).length;
    const achGrid = ach.slice(0, 8).map(([ico, name, , ok]) => `
      <div class="ach ${ok ? "on" : ""}"><div class="medal">${medal(ico)}</div><div class="l">${esc(name)}</div></div>`).join("");

    screen.innerHTML = `
      <div class="me-hero">
        <div class="ava"><img src="${LOGO}" alt=""></div>
        <div class="nm">${esc(me.name)}</div>
        <div class="rt">${esc(me.rank)} · рейтинг <b>${me.rating}</b></div>
        <div class="xp">
          <div class="bar"><i style="width:${progress(me)}%"></i></div>
          <div class="cap"><span>${me.rating} / ${me.next ? me.next.at : me.rating}</span><span>${me.next ? esc(me.next.rank) : "максимум"}</span></div>
        </div>
      </div>
      <div class="stats">
        <div class="stat"><b>${icon("fire")} ${me.streak}</b><span>серия</span></div>
        <div class="stat"><b>${me.solved}/${me.total}</b><span>задач</span></div>
        <div class="stat"><b>${p.place || "—"}</b><span>место${p.players ? " из " + p.players : ""}</span></div>
      </div>
      <div class="reward-widget">
        <div class="rw-title">Прогресс дня</div>
        <div class="rw-grid">
          <div><b>${icon("fire")} ${me.streak} дн.</b><span>рекорд ${me.best_streak}</span></div>
          <div><b>Уроки ${p.lessons_done_today || 0}/${p.lessons_goal || 3}</b><span>пройдено сегодня</span></div>
        </div>
        <div class="bar"><i style="width:${Math.min(100, Math.round(((p.lessons_done_today || 0) / (p.lessons_goal || 3)) * 100))}%"></i></div>
      </div>
      <button class="card" data-go="learn"><div class="ico">${icon("star")}</div><div class="main"><div class="t">Знания: ${me.knowledge || 0}</div><div class="s">Очки за статьи в Обучении, отдельно от рейтинга</div></div><div class="arrow">›</div></button>
      <div class="h2">Достижения <small>${achDone} / ${ach.length}</small></div>
      <div class="ach-grid" data-go="ach">${achGrid}</div>
      <div class="h2">Звания</div><div class="ranks">${ranks}</div>
      <div class="h2">Очки за 2 недели</div><div class="chart">${chart}</div>
      <div class="h2">Мои ходы <small>${total || ""}</small></div>
      ${total ? `<div class="marks">${marks}</div>` : '<p class="muted">Реши первую задачу — тут появится, как ты ходишь</p>'}
      ${p.games ? `<div class="h2">Партии с ИИ</div><p>${p.games} сыграно · побед: ${p.wins}</p>` : ""}`;
  }

  const errorHtml = () => `<div class="empty"><img src="${LOGO}" alt=""><p class="muted">Не загрузилось. Проверь интернет</p>
    <button class="btn ghost" onclick="location.reload()">Обновить</button></div>`;

  // ---------- разбор остальных ходов ----------
  function othersHtml(list) {
    if (!list || !list.length) return "";
    return `<div class="v-card"><div class="lbl">Разбор других ходов</div>${list.map((o) => `
      <div class="other">${markIcon(o.mark, "ic other-ic")}<div><b>«${esc(o.text)}»</b><br><span class="muted">${esc(o.why)}</span></div></div>`).join("")}</div>`;
  }
  function markIcon(mark, cls = "ic") {
    return MARK_IMG[mark] ? icon(MARK_IMG[mark], cls)
      : `<span class="mk-txt" style="--c:${(MARKS[mark] || MARKS["?!"]).c}">${esc(mark)}</span>`;
  }

  // ---------- бета-тест ----------
  function betaBar() {
    const b = $("#beta-bar");
    if (!state.beta) return;
    b.innerHTML = state.beta.on
      ? `<span>🧪 Бета-тест · что-то может быть сырым</span><button data-feedback>Отзыв</button>`
      : `<span>${icon("knight")} Рейтинг обнулён — все начинают на равных</span><button data-feedback>Отзыв</button>`;
    b.classList.remove("hidden");
    document.body.classList.add("with-beta");
  }

  function renderClosed(res) {
    $("#tabs").classList.add("hidden");
    const b = state.beta;
    const queue = res && !res.ok
      ? `<div class="v-card">${icon("timer")} Мест нет — ты в очереди: <b>${res.num}-й</b>. Позовём на релиз, уже скоро</div>`
      : `<button class="btn big" id="join">Занять место в тесте</button>`;
    screen.innerHTML = `
      <div class="hero"><img src="${LOGO}" alt="">
        <div class="brand">Шах и <span>Чат</span></div>
        <div class="tagline">Закрытый бета-тест · ${b.slots} мест</div>
      </div>
      <div class="v-card">Первые ${b.slots} самых быстрых играют в новую версию: партии по переписке как в шахматах, рейтинг Эло, разбор каждого хода. Условие одно — после пары партий оставить отзыв</div>
      ${queue}`;
    const j = $("#join");
    if (j) j.onclick = async () => {
      j.disabled = true;
      try {
        const r = await api("beta/join", {});
        if (r.ok) { haptic("success"); toast(r.num ? `Ты в тесте! Место ${r.num} из ${r.slots}` : "Ты в тесте!"); $("#tabs").classList.remove("hidden"); return load(); }
        haptic("warning"); renderClosed(r);
      } catch (e) { j.disabled = false; toast("Не получилось, попробуй ещё раз"); }
    };
  }

  function openFeedback(required) {
    const m = $("#modal");
    let stars = 0;
    m.innerHTML = `<div class="verdict-in fb">
      <div class="title">${required ? "Как тебе «Шах и Чат»?" : "Оставить отзыв"}</div>
      <p class="muted">${required ? "Ты прошёл 15 задач. Напиши, что оставить, что поправить и чего не хватает — и продолжай играть." : "Что улучшить в игре? Отзыв прочитает автор."}</p>
      <div class="stars" id="stars">${[1, 2, 3, 4, 5].map((n) => `<button data-s="${n}">★</button>`).join("")}</div>
      <textarea id="fb-text" rows="5" maxlength="2000" placeholder="Что понравилось? Что сырое или непонятно? Какую ситуацию добавить?"></textarea>
      <button class="btn" id="fb-send">Отправить</button>
      ${required ? "" : '<button class="btn ghost" id="fb-close" style="margin-top:10px">Позже</button>'}
    </div>`;
    m.classList.remove("hidden");
    $("#stars").onclick = (e) => {
      const b = e.target.closest("button"); if (!b) return;
      stars = +b.dataset.s; haptic("tap");
      [...$("#stars").children].forEach((x) => x.classList.toggle("on", +x.dataset.s <= stars));
    };
    if (!required) $("#fb-close").onclick = () => m.classList.add("hidden");
    $("#fb-send").onclick = async () => {
      // как на сервере: без невидимых символов и хотя бы 5 букв
      const text = $("#fb-text").value.replace(/[\u00ad\u061c\u115f\u1160\u180e\u200b-\u200f\u202a-\u202e\u2060-\u206f\u2800\u3164\ufeff\uffa0]/g, "").replace(/\s+/g, " ").trim();
      if ((text.match(/\p{L}/gu) || []).length < 5) { toast("Напиши пару слов — это очень поможет"); return; }
      try {
        await api("feedback", { stars: stars || null, text });
        haptic("success"); m.classList.add("hidden"); toast("Спасибо! Отзыв ушёл автору");
        if (state.beta) { state.beta.feedback = true; state.beta.need_feedback = false; }
      } catch (e) { toast("Не отправилось, попробуй ещё раз"); }
    };
  }

  // ---------- партии ----------
  const RESULT = { win: ["ПОБЕДА", "Она в игре — ты провёл партию", "var(--green)"], stalemate: ["ПАТ", "Разговор угас: никто не выиграл", "var(--m-dub)"], mate: ["МАТ", "Партия проиграна — разбираем ошибки", "var(--m-blunder)"] };
  const stars = (r) => "★".repeat(Math.max(1, Math.min(5, Math.floor(r / 250) + 1)));
  let battle = null; // текущая партия
  // «Блиц» (19.11): 30 с на ход, по желанию. Выбор помним в браузере
  const pref = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  let blitzOn = pref("blitz") === "1";

  async function renderPartii() {
    screen.innerHTML = `<div class="title">Партии</div><p class="subtitle">Живые переписки. Каждый ход — оценка, как в шахматах</p>${'<div class="skel"></div>'.repeat(4)}`;
    let data;
    try { data = await api("partii"); } catch (e) { screen.innerHTML = errorHtml(); return; }
    if (tab !== "partii") return;
    if (data.beta) state.beta = data.beta;
    screen.innerHTML = `<div class="title">Партии</div><p class="subtitle">Живые переписки. Каждый ход — оценка, как в шахматах. Рейтинг соперницы — по Эло</p>
      ${levelHtml(data.level)}
      <button class="card toggle${blitzOn ? " on" : ""}" id="blitz-tg"><div class="ico">⏱</div>
        <div class="main"><div class="t">Блиц</div><div class="s">30 секунд на ход. Не успел — ход ??</div></div><div class="switch"><i></i></div></button>
      ${data.items.map((p) => {
        const r = p.result && RESULT[p.result];
        return `<button class="card partiya" data-partiya="${esc(p.id)}">
          <div class="ico">${icon(p.rating >= 900 ? "queen" : p.rating >= 500 ? "rook" : "pawn")}</div>
          <div class="main"><div class="t">${esc(p.title)}</div>
            <div class="s">Эло ${p.rating} · <span class="gold">${stars(p.rating)}</span> · ${p.moves} хода</div>
            ${r ? `<div class="s" style="color:${r[2]}">${r[0]} · точность ${p.accuracy}%</div>` : `<div class="s">${esc(p.intro)}</div>`}
          </div><div class="arrow">${r ? "↻" : "›"}</div></button>`;
      }).join("")}`;
  }

  async function startPartiya(id) {
    if (state.beta && state.beta.need_feedback) return openFeedback(true);
    let g;
    try { g = await api("partiya/start", { id, blitz: blitzOn }); } catch (e) {
      if (e.code === "need_feedback") return openFeedback(true);
      toast("Не получилось начать"); return;
    }
    battle = { ...g, log: [], marks: [], busy: false };
    battle.log.push({ who: "sys", text: g.partiya.intro + (g.blitz ? ` · Блиц: ${g.seconds} с на ход` : "") });
    go("battle");
    await herSays(g.step.her);
    battle.options = g.step.options;
    battle.n = g.step.n; battle.total = g.step.total;
    startClock();
    drawBattle();
  }

  // таймер блица: дедлайн хода, полоска обновляется сама
  function startClock() { if (battle && battle.blitz) battle.deadline = Date.now() + (battle.seconds || 30) * 1000; }
  setInterval(() => {
    if (!battle || !battle.deadline) return;
    if (tab !== "battle") { battle.deadline = null; return; }
    const left = battle.deadline - Date.now();
    const bar = $("#btimer i");
    if (bar) { bar.style.width = `${Math.max(0, left / ((battle.seconds || 30) * 10))}%`; bar.parentElement.classList.toggle("low", left < 10000); }
    if (left <= 0) timeoutMove();
  }, 200);

  async function timeoutMove() {
    if (!battle || battle.busy) return;
    battle.busy = true; battle.deadline = null; haptic("error");
    let res;
    try { res = await api("partiya/move", { game_id: battle.game_id, timeout: true }); }
    catch (e) { battle.busy = false; startClock(); toast("Не получилось, попробуй ещё раз"); return; }
    battle.marks.push(res.mark);
    battle.log.push({ who: "me", text: "⏳ долго думал…", mark: res.mark });
    battle.pending = true; drawBattle();
    showMoveVerdict(res);
  }

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  async function herSays(lines) {
    for (const t of lines) {
      battle.typing = true; drawBattle(); await sleep(DEMO ? 350 : 650 + Math.min(900, t.length * 18));
      battle.typing = false; battle.log.push({ who: "her", text: t }); drawBattle();
    }
  }

  function evalPct() {
    if (!battle.marks.length) return 50;
    const S = { "!!": 1, "#": 1, "!": .8, "!?": .6, "?!": .35, "?": .15, "??": 0 };
    const avg = battle.marks.reduce((a, m) => a + (S[m] ?? .35), 0) / battle.marks.length;
    return Math.round(8 + avg * 84);
  }

  function renderBattle() { if (!battle) return go("partii"); drawBattle(); }

  function drawBattle() {
    if (tab !== "battle" || !battle) return;
    const p = battle.partiya, me = state.me;
    const notation = battle.marks.map((m, i) => `<span class="nt" style="--c:${(MARKS[m] || MARKS["?!"]).c}">${i + 1}. ${esc(m)}</span>`).join("");
    const chat = battle.log.map((m) => m.who === "sys" ? `<div class="sys">${esc(m.text)}</div>`
      : m.who === "her" ? `<div class="msg her"><div class="bubble">${esc(m.text)}</div></div>`
      : `<div class="msg me"><div class="bubble mine">${esc(m.text)}</div>${m.mark ? markIcon(m.mark, "ic msg-mark") : ""}</div>`).join("")
      + (battle.typing ? `<div class="msg her"><div class="bubble typing"><i></i><i></i><i></i></div></div>` : "");
    const opts = !battle.final && !battle.typing && battle.options && !battle.pending
      ? `${battle.deadline ? '<div class="btimer"><i></i></div>' : ""}<div class="your-move">Твой ход · ${battle.n} из ${battle.total}${battle.blitz ? " · блиц" : ""}</div>
         <div class="moves" id="bmoves">${battle.options.map((o) => `<button class="move" data-idx="${o.idx}">${esc(o.text)}</button>`).join("")}</div>` : "";
    screen.innerHTML = `
      <div class="board-top">
        <button class="back" data-go="partii">‹</button>
        <div class="player"><div class="av her-av">${icon("queen")}</div><div><b>${esc(p.title)}</b><span>Эло ${p.rating}</span></div></div>
        <div class="clock">${battle.n || 1}/${battle.total || p.moves}</div>
      </div>
      <div class="notation">${notation || '<span class="muted">Нотация партии появится здесь</span>'}${battle.rated ? "" : ' <span class="muted">· без рейтинга</span>'}</div>
      <div class="board">
        <div class="evalbar"><i style="height:${evalPct()}%"></i></div>
        <div class="board-chat" id="bchat">${chat}</div>
      </div>
      <div class="board-bottom"><div class="player"><div class="av knight"><img src="${LOGO}" alt=""></div><div><b>Ты</b><span>Эло ${me.rating}</span></div></div></div>
      ${opts}`;
    const c = $("#bchat"); if (c) c.scrollTop = c.scrollHeight;
    const bm = $("#bmoves");
    if (bm) bm.onclick = (e) => { const b = e.target.closest(".move"); if (b) playMove(b); };
  }

  async function playMove(el) {
    if (battle.busy) return;
    battle.busy = true; battle.deadline = null; haptic("tap");
    const text = el.textContent;
    let res;
    try { res = await api("partiya/move", { game_id: battle.game_id, idx: +el.dataset.idx }); }
    catch (e) { battle.busy = false; toast("Не получилось, попробуй ещё раз"); return; }
    battle.marks.push(res.mark);
    battle.log.push({ who: "me", text, mark: res.mark });
    battle.pending = true; drawBattle();
    haptic(["!!", "!", "#"].includes(res.mark) ? "success" : res.mark === "??" ? "error" : "warning");
    showMoveVerdict(res);
  }

  function showMoveVerdict(res) {
    const mk = MARKS[res.mark] || MARKS["?!"];
    const v = $("#verdict");
    v.innerHTML = `<div class="verdict-in" style="--c:${mk.c}">
      ${MARK_IMG[res.mark] ? icon(MARK_IMG[res.mark], "badge-img sm") : `<div class="badge">${esc(res.mark)}</div>`}
      <div class="v-name">${esc(res.name)}</div>
      <div class="v-card"><div class="lbl">Почему</div>${esc(res.why)}</div>
      ${res.best ? `<div class="v-card"><div class="lbl">Лучший ход</div>«${esc(res.best)}»</div>` : ""}
      ${othersHtml(res.others)}
      <button class="btn" id="v-go">${res.final ? "Итог партии" : "Смотреть её ответ"}</button>
    </div>`;
    v.classList.remove("hidden");
    $("#v-go").onclick = async () => {
      v.classList.add("hidden");
      await herSays([res.reply]);
      if (res.final) { battle.final = res.final; return showFinal(res.final); }
      await herSays(res.next.her);
      battle.options = res.next.options; battle.n = res.next.n;
      battle.pending = false; battle.busy = false; startClock(); drawBattle();
    };
  }

  function showFinal(f) {
    state.me = f.me;
    const r = RESULT[f.result] || RESULT.stalemate;
    const sign = f.delta > 0 ? "+" : "";
    const reviewHtml = (f.review || []).map((turn) => `
      <article class="recap-turn">
        <div class="lbl">Ход ${turn.turn}</div>
        ${(turn.her || []).map((line) => `<div class="recap-her">Она: ${esc(line)}</div>`).join("")}
        ${turn.options.every((o) => !o.selected) ? `<div class="recap-option selected"><div class="recap-option-head"><b>${esc(turn.name)}</b><span>твой ответ</span></div><div>«${esc(turn.move)}»</div><div class="muted">${esc(turn.why)}</div></div>` : ""}
        <div class="recap-options">${(turn.options || []).map((o) => `
          <div class="recap-option ${o.selected ? "selected" : ""}">
            <div class="recap-option-head"><b>${esc(o.name)}</b>${o.selected ? '<span>твой ответ</span>' : ""}</div>
            <div>«${esc(o.text)}»</div><div class="muted">${esc(o.why)}</div>
          </div>`).join("")}</div>
        <div class="recap-her">Она ответила: ${esc(turn.reply)}</div>
      </article>`).join("");
    const v = $("#verdict");
    v.innerHTML = `<div class="verdict-in final">
      <div class="result" style="color:${r[2]}">${r[0]}</div>
      <div class="muted center">${r[1]}</div>
      <div class="final-stats">
        <div><b>${f.accuracy}%</b><span>точность</span></div>
        <div><b>${f.rated ? `${f.before} → ${f.after}` : f.after}</b><span>${f.rated ? `Эло ${sign}${f.delta}` : "без рейтинга (переигровка)"}</span></div>
        <div><b>${f.expected}%</b><span>шанс по Эло</span></div>
      </div>
      ${f.rank_up ? `<div class="rankup">${piece(f.me.rank)} Новое звание: ${esc(f.me.rank)}</div>` : ""}
      <div class="v-card"><div class="lbl">Ходы партии</div><div class="notation big">${f.marks.map((m, i) => `<span class="nt" style="--c:${(MARKS[m] || MARKS["?!"]).c}">${i + 1}. ${esc(m)}</span>`).join("")}</div></div>
      ${reviewHtml ? `<details class="v-card recap"><summary>Разбор всех ходов</summary>${reviewHtml}</details>` : ""}
      <button class="btn" id="f-next">К партиям</button>
      <div class="row"><button class="btn ghost" id="f-again">Переиграть</button><button class="btn ghost" data-feedback>Отзыв</button></div>
    </div>`;
    v.classList.remove("hidden");
    haptic(f.result === "win" ? "success" : f.result === "mate" ? "error" : "warning");
    const id = battle.partiya.id;
    $("#f-next").onclick = () => { v.classList.add("hidden"); battle = null; go("partii"); if (f.need_feedback) { state.beta.need_feedback = true; openFeedback(true); } };
    $("#f-again").onclick = () => { v.classList.add("hidden"); if (f.need_feedback) { state.beta.need_feedback = true; return openFeedback(true); } startPartiya(id); };
    profile = null;
  }

  // ---------- навигация ----------
  const TAB_OF = { home: "home", partii: "partii", battle: "partii", game: "game", top: "top", profile: "profile", learn: "home", ach: "profile" };
  function go(name) {
    tab = name;
    document.body.classList.toggle("in-battle", name === "battle");
    [...$("#tabs").children].forEach((b) => b.classList.toggle("active", b.dataset.tab === TAB_OF[name]));
    window.scrollTo(0, 0);
    ({ home: renderHome, partii: renderPartii, battle: renderBattle, game: renderGame, top: renderTop, learn: renderLearn, ach: renderAch, profile: renderProfile })[name]();
  }

  $("#tabs").onclick = (e) => {
    const b = e.target.closest("button");
    if (b && b.dataset.tab !== tab) { haptic("tap"); go(b.dataset.tab); }
  };
  document.addEventListener("click", (e) => {
    const g = e.target.closest("[data-go]");
    if (g) { haptic("tap"); $("#verdict").classList.add("hidden"); go(g.dataset.go); return; }
    const b = e.target.closest("[data-bot]");
    if (b) { openBot(b.dataset.bot); return; }
    if (e.target.closest("[data-feedback]")) { openFeedback(false); return; }
    const lv = e.target.closest("[data-level]");
    if (lv) { setLevel(lv.dataset.level); return; }
    if (e.target.closest("#blitz-tg")) {
      blitzOn = !blitzOn; pref("blitz", blitzOn ? "1" : "0"); haptic("tap");
      e.target.closest("#blitz-tg").classList.toggle("on", blitzOn);
      toast(blitzOn ? "Блиц включён: 30 секунд на ход" : "Блиц выключен");
      return;
    }
    const pl = e.target.closest("[data-partiya]");
    if (pl) { haptic("tap"); startPartiya(pl.dataset.partiya); return; }
    if (e.target.closest("[data-invite]")) {
      shareLink("drug", "Тренажёр переписки «Шах и Чат»: ситуация из чата — твой ход — оценка как в шахматах. Залетай");
      return;
    }
    const a = e.target.closest("a[data-ext]");
    if (a && tg && tg.openLink) { e.preventDefault(); tg.openLink(a.href); }
  });

  async function load() {
    screen.innerHTML = '<div class="skel"></div>'.repeat(4);
    try {
      state = await api("state");
    } catch (e) {
      const msg = e.code === "no_user"
        ? `<div class="title">Сначала зайди в бота</div><p class="muted">Нажми «Старт» в чате с ботом — и возвращайся сюда</p>`
        : e.code === "banned" ? `<p class="muted">Доступ закрыт</p>` : "";
      screen.innerHTML = msg ? `<div class="empty"><img src="${LOGO}" alt="">${msg}</div>` : errorHtml();
      return;
    }
    if (state.beta && state.beta.on && !state.beta.tester) return renderClosed();
    betaBar();
    if (state.beta && state.beta.need_feedback) openFeedback(true);
    const start = (location.hash || "").slice(1).split(/[&?]/)[0];
    go(TAB_OF[start] && start !== "battle" ? start : "home");
    if (start === "feedback" && !(state.beta && state.beta.need_feedback)) openFeedback(false);
  }

  // ---------- демо без Telegram ----------
  const DEMO_P = [
    { chat: "Она: «Меня повысили!!»", moves: [["Норм", "?!", "Сухо: человек делится радостью, а ты её гасишь"], ["Поздравляю!! Как это было? Отмечаем?", "!!", "Активная поддержка хороших новостей укрепляет отношения (Gable, 2004)"], ["Теперь будешь пропадать на работе", "??", "Обесценил радость — зевок"]] },
    { chat: "Мэтч. Пустой чат. Твой первый ход", moves: [["Привет", "?!", "«Привет» получает ответ реже, чем сообщение по анкете"], ["Вижу, ты любишь горы — где было самое красивое место?", "!!", "Зацепка за анкету + открытый вопрос"], ["Ты очень красивая", "??", "Комплимент внешности первым сообщением работает хуже всего"]] },
  ];
  const D = { rating: 87, solved: 5, streak: 3 };
  const DEMO_ART = (id, text) => ({ id, text, tip: "После ответа спроси «а почему?»", source: "Huang и др., 2017", url: null, opened: false, answered: false, ok: null, correct: null, reward: 3, earned: false,
    question: "Кто чаще получал второе свидание?", options: [{ idx: 1, text: "кто больше и подробнее рассказывал о себе" }, { idx: 0, text: "кто задавал больше уточняющих вопросов" }, { idx: 2, text: "кто чаще шутил и делал комплименты" }] });
  const DEMO_LEARN = { per_day: 3, reward: 3, points: 12, done: 0, total_read: 4, all: 36, items: [
    DEMO_ART("a1", "Кто задаёт больше вопросов, особенно уточняющих, тот нравится собеседнику сильнее"),
    DEMO_ART("a2", "После разговора люди стабильно недооценивают, насколько понравились собеседнику"),
    DEMO_ART("a3", "Только около 2% разговоров заканчиваются тогда, когда этого хотят оба") ] };
  const demoRank = (r) => [...RANKS].reverse().find((x) => r >= x[2]);
  function demoMe() {
    const rk = demoRank(D.rating);
    const nx = RANKS.find((x) => x[2] > D.rating);
    return { name: "Артемий", rating: D.rating, rank: rk[0], rank_from: rk[2], next: nx ? { at: nx[2], rank: nx[0] } : null, streak: D.streak, best_streak: 4, solved: D.solved, total: 39, level: D.level || "start" };
  }
  const demoPuzzle = (i) => (i < DEMO_P.length ? { id: i, number: D.solved + 1, daily: i === 0, chat: DEMO_P[i].chat, moves: DEMO_P[i].moves.map((m, idx) => ({ idx, text: m[0] })) } : null);
  let demoI = 0;
  const DG = { step: 0, steps: [
    { her: ["🎤 «Ну он вроде милый, но пишет как робот, через точки»", "БЛИН", "ЭТО БЫЛО НЕ ТЕБЕ 🙈🙈🙈"], options: [
      ["Ахах, расслабься 😄 зато теперь знаю, что пора перестать писать как робот. Отвечаю без точек: нравишься", "!!", "Снял её стыд юмором и честно ответил на её же вопрос", "Боже 🙈 я сейчас сгорю. Но… приятно)"],
      ["Ничего страшного.", "?", "Та самая точка — читается холодно (Klin, 2016)", "Ну всё, ты обиделся"],
      ["Интересно, что ты ещё обо мне рассказываешь", "??", "Подозрение вместо лёгкости", "Да ничего такого…"]] },
    { her: ["Только подруге не говори, что ты слышал 😅"], options: [
      ["Могила. Но с тебя ответ: а я тебе нравлюсь? 😏", "!!", "Открытость за открытость", "Ну… ты сам понимаешь 😊"],
      ["Ок", "?!", "Она тянется, а ты односложно", "Ты точно не обиделся?"],
      ["А что мне за молчание будет?", "!?", "Флирт с подмигиванием — рискованно, но тепло", "Кофе с меня 😄"]] },
  ] };
  async function demo(path, body) {
    await new Promise((r) => setTimeout(r, 200));
    if (path === "state") return { me: demoMe(), puzzle: demoPuzzle(demoI), daily_done: false, bot: "vibemeter_bot", beta: { on: true, tester: !/closed/.test(location.search), slots: 30, feedback: false, games: 0, need_feedback: false } };
    if (path === "beta/join") return { ok: false, num: 12, total: 30, slots: 30 };
    if (path === "feedback") return { ok: true };
    if (path === "level") { D.level = body.level; return { me: demoMe(), puzzle: demoPuzzle(demoI), daily_done: false }; }
    if (path === "partii") return { level: D.level || "start", items: [
      { id: "povyshenie", title: "Её повысили", rating: 200, intro: "Вы общаетесь две недели. Вечер, она пишет первой", moves: 4, result: "win", accuracy: 88 },
      { id: "golosovoe", title: "Голосовое не тебе", rating: 600, intro: "Она отправила тебе голосовое — явно для подруги", moves: 4, result: null },
      { id: "byvshaya", title: "Бывшая в 3 ночи", rating: 1000, intro: "Вы расстались полгода назад. 03:07, приходит", moves: 4, result: "mate", accuracy: 35 },
    ] };
    if (path === "partiya/start") { DG.step = 0; return { game_id: 1, rated: true, blitz: !!body.blitz, seconds: 30, partiya: { id: "golosovoe", title: "Голосовое не тебе", rating: 600, intro: "Вы переписываетесь неделю. Она отправила тебе голосовое — явно для подруги", moves: 2 }, step: { n: 1, total: 2, her: DG.steps[0].her, options: DG.steps[0].options.map((o, idx) => ({ idx, text: o[0] })) } }; }
    if (path === "partiya/move") {
      const st = DG.steps[DG.step]; const o = body.timeout ? ["(долго думал)", "??", "30 секунд прошли. Пока ты думал, она ушла в другой чат", "ладно, мне тут пишут, потом отвечу"] : st.options[body.idx]; DG.step++;
      const res = { mark: o[1], name: MARKS[o[1]].name, why: o[2], reply: o[3], best: o[1] === "!!" ? null : st.options.find((x) => x[1] === "!!")[0], others: st.options.filter((x) => x !== o).map((x) => ({ text: x[0], mark: x[1], why: x[2] })) };
      if (DG.step < DG.steps.length) res.next = { n: DG.step + 1, total: 2, her: DG.steps[DG.step].her, options: DG.steps[DG.step].options.map((x, idx) => ({ idx, text: x[0] })) };
      else res.final = { result: "win", rated: true, before: D.rating, after: D.rating + 31, delta: 31, accuracy: 90, marks: ["!!", "!"], expected: 23, rank_up: false, me: demoMe(), need_feedback: false };
      return res;
    }
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
      const names = ["Дима", "Алина", "Кирилл", "Даня", "Соня", "Егор", "Вика"];
      const items = names.map((n, i) => ({ place: i + 1, name: n, points: 420 - i * 47, rank: demoRank(420 - i * 47)[0], me: false }));
      return { items, me: { place: 14, points: D.rating, total: 120 } };
    }
    if (path === "learn") return DEMO_LEARN;
    if (path === "learn/open") return { ok: true };
    if (path === "learn/quiz") {
      const it = DEMO_LEARN.items.find((x) => x.id === body.id);
      Object.assign(it, { answered: true, ok: body.idx === 0, correct: "кто задавал больше уточняющих вопросов", earned: body.idx === 0, reward: 0 });
      DEMO_LEARN.done = DEMO_LEARN.items.filter((x) => x.answered).length;
      return { ok: body.idx === 0, correct: it.correct, delta: body.idx === 0 ? 3 : 0, me: null, learn: DEMO_LEARN };
    }
    if (path === "facts") {
      const f = (t, tip, s) => ({ id: t, text: t, tip, source: s, url: null });
      return { day: f("Кто задаёт больше уточняющих вопросов, тот нравится собеседнику сильнее", "Спроси «а почему?» после ответа", "Huang и др., 2017"),
        items: [f("После разговора люди недооценивают, насколько понравились собеседнику", "Скорее всего, ты понравился больше, чем думаешь", "Boothby и др., 2018")] };
    }
    if (path === "profile") {
      const today = Date.now() + 3 * 3600e3;
      const days = [0, 1, 3, 4, 7].map((i, k) => ({ day: new Date(today - i * 86400e3).toISOString().slice(0, 10), pts: [23, 15, -5, 30, 8][k] }));
      return { me: demoMe(), marks: { "!!": 3, "!": 4, "?!": 2, "??": 1 }, days, games: 2, wins: 1, solved_today: 1, place: 14, players: 120 };
    }
    return {};
  }

  load();
})();
