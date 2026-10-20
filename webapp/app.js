/* Вайбометр Mini App. Без Telegram (initData пустой) работает в демо-режиме на моках. */
"use strict";

const tg = window.Telegram && window.Telegram.WebApp;
const DEMO = !tg || !tg.initData;

if (tg) {
  tg.ready();
  tg.expand();
  try { tg.setHeaderColor("#07060d"); tg.setBackgroundColor("#07060d"); } catch (_) {}
}

// =========================================================
// Иконки (inline SVG, stroke = currentColor)
// =========================================================
const I = {
  home: '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
  heart: '<path d="M12 20s-7-4.4-9.2-8.6C1.2 8.3 3 4.5 6.6 4.5c2.1 0 3.4 1.2 4.4 2.6 1-1.4 2.3-2.6 4.4-2.6 3.6 0 5.4 3.8 3.8 6.9C19 15.6 12 20 12 20z"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.2-4 4.3-6 8-6s6.8 2 8 6"/>',
  game: '<rect x="2" y="7" width="20" height="11" rx="5"/><path d="M7 11v3M5.5 12.5h3M15 12h.01M18 13.5h.01"/>',
  crown: '<path d="M3 8l4.5 4L12 5l4.5 7L21 8l-2 11H5z"/>',
  chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
  flag: '<path d="M5 21V4h11l-1.5 4L16 12H5"/>',
  chev: '<path d="M9 6l6 6-6 6"/>',
};
const svg = (name) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${I[name]}</svg>`;

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function plural(n, one, few, many) {
  const a = Math.abs(n) % 100, b = a % 10;
  if (a > 10 && a < 20) return many;
  if (b > 1 && b < 5) return few;
  if (b === 1) return one;
  return many;
}
const days = (n) => `${n} ${plural(n, "день", "дня", "дней")}`;

function haptic(type) {
  try {
    if (!tg || !tg.HapticFeedback) return;
    if (type === "success" || type === "error") tg.HapticFeedback.notificationOccurred(type);
    else tg.HapticFeedback.impactOccurred(type || "light");
  } catch (_) {}
}

function toast(text) {
  const t = document.getElementById("toast");
  t.textContent = text;
  t.classList.remove("hidden");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.add("hidden"), 2200);
}

// =========================================================
// API
// =========================================================
const api = DEMO ? makeDemoApi() : {
  async call(path, body) {
    const res = await fetch(`api/${path}`, {
      method: body ? "POST" : "GET",
      headers: { "X-Init-Data": tg.initData, "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.error || res.status), { code: data.error, status: res.status });
    return data;
  },
  me() { return this.call("me"); },
  next() { return this.call("next"); },
  vibe(id, action) { return this.call("vibe", { id, action }); },
  vibes() { return this.call("vibes"); },
  setSearch(value) { return this.call("settings", { search_gender: value }); },
  question(id, text) { return this.call("question", { id, text }); },
  report(id, reason) { return this.call("report", { id, reason }); },
  async photo(id) {
    const res = await fetch(`api/photo/${id}`, { headers: { "X-Init-Data": tg.initData } });
    if (!res.ok) return null;
    return URL.createObjectURL(await res.blob());
  },
};

function makeDemoApi() {
  const me = {
    id: 1, name: "Артемий", age: 19, city: "Псков", username: "demo",
    interests: ["баскетбол", "музыка", "бизнес", "технологии"],
    about: "Развиваюсь. Создаю. Ищу своих",
    gender: "male", search_gender: "female", has_photo: false,
  };
  const people = [
    { id: 11, name: "Анастасия", age: 19, city: "Псков", interests: ["музыка", "спорт", "кино"], about: "Люблю музыку, спорт и красивые закаты", vibe: 78, common: ["музыка"], likes_me: true },
    { id: 12, name: "Вика", age: 21, city: "Псков", interests: ["технологии", "путешествия", "кофе"], about: "Фронтенд днём, горы по выходным", vibe: 64, common: ["технологии"] },
    { id: 13, name: "Полина", age: 20, city: "Санкт-Петербург", interests: ["книги", "театр"], about: "Читаю быстрее, чем пишу", vibe: 31, common: [] },
    { id: 14, name: "Даша", age: 22, city: "Псков", interests: ["бизнес", "музыка", "баскетбол"], about: "Запускаю кофейню и хожу на баскет", vibe: 92, common: ["бизнес", "музыка", "баскетбол"], likes_me: true },
  ];
  const stats = { streak_days: 1, best_streak: 3, likes_sent: 1, likes_received: 2, mutual_likes: 1, games: 1, questions_sent: 0, questions_received: 0 };
  const achievements = [
    ["👑", "Новичок", "заполнил анкету", 1, 1],
    ["🩷", "Первый вайб", "первый лайк", 1, 1],
    ["💎", "Взаимность", "первый взаимный вайб", 1, 1],
    ["🔥", "В огне", "серия 7 дней", 3, 7],
    ["💘", "Сердцеед", "25 лайков", 1, 25],
    ["🍭", "Душа компании", "10 игр", 1, 10],
    ["⚡", "Болтун", "10 вопросов", 0, 10],
    ["⭐", "Магнит", "тебя выбрали 25 раз", 2, 25],
    ["🏆", "Легенда", "серия 30 дней", 3, 30],
  ].map(([icon, name, hint, value, goal]) => ({ icon, name, hint, value, goal, done: value >= goal }));
  let queue = people.slice();
  const mutual = [{ id: 15, name: "Соня", age: 20, city: "Псков", username: "demo", has_photo: false }];
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));

  return {
    async me() {
      await wait(150);
      const done = achievements.filter((a) => a.done).length;
      return { user: me, stats, achievements, level: levelFor(done, achievements.length) };
    },
    async next() { await wait(200); return { candidate: queue[0] || null }; },
    async vibe(id, action) {
      await wait(150);
      const p = queue.find((x) => x.id === id);
      queue = queue.filter((x) => x.id !== id);
      if (action === "like") {
        stats.likes_sent += 1;
        if (p && p.likes_me) {
          stats.mutual_likes += 1;
          mutual.unshift({ ...p, username: "demo", has_photo: false });
          return { mutual: true, match: { ...p, username: "demo", has_photo: false } };
        }
      }
      return { mutual: false };
    },
    async vibes() {
      await wait(150);
      return { incoming: queue.filter((p) => p.likes_me), mutual };
    },
    async setSearch(v) { me.search_gender = v; return { ok: true }; },
    async question() { await wait(300); return { ok: true }; },
    async report(id) { await wait(200); queue = queue.filter((x) => x.id !== id); return { ok: true }; },
    async photo() { return null; },
  };
}

// Уровни считаются по числу открытых достижений (сервер отдаёт то же самое)
function levelFor(done, total) {
  const levels = [[0, "Новичок"], [2, "В теме"], [4, "Вайбер"], [6, "Звезда"], [total, "Легенда"]];
  let n = 1, name = levels[0][1], nextAt = levels[1][0];
  levels.forEach(([at, nm], i) => { if (done >= at) { n = i + 1; name = nm; nextAt = levels[i + 1] ? levels[i + 1][0] : total; } });
  return { n, name, done, total, next_at: nextAt };
}

// =========================================================
// Состояние и навигация
// =========================================================
const state = { me: null, vibes: null, candidate: null, photos: {} };

const NAV = [
  { id: "home", label: "Главная", icon: "home" },
  { id: "search", label: "Поиск вайба", short: "Поиск", icon: "search", tab: true },
  { id: "vibes", label: "Мои вайбы", short: "Вайбы", icon: "heart", tab: true },
  { id: "games", label: "Игры", icon: "game", tab: true },
  { id: "profile", label: "Профиль", icon: "user", tab: true },
  { id: "fame", label: "Зал славы", icon: "crown" },
  { id: "stats", label: "Статистика", icon: "chart" },
  { id: "settings", label: "Настройки", icon: "gear" },
];
const TABS = ["home", "search", "vibes", "games", "profile"];

function route() { return (location.hash || "#home").slice(1); }
function go(id) { if (route() === id) render(); else location.hash = id; }
window.addEventListener("hashchange", () => {
  document.getElementById("overlay").classList.add("hidden");
  closeSheet();
  render();
});

function renderNav() {
  const r = route();
  const incoming = state.vibes ? state.vibes.incoming.length : 0;
  document.getElementById("side-nav").innerHTML = NAV.map((n) =>
    `<button class="side-link ${r === n.id ? "active" : ""}" data-go="${n.id}">${svg(n.icon)}<span>${n.label}</span></button>`
  ).join("");
  document.getElementById("tabbar").innerHTML = TABS.map((id) => {
    const n = NAV.find((x) => x.id === id);
    const dot = id === "vibes" && incoming ? `<span class="dot">${incoming}</span>` : "";
    return `<button class="tab ${r === id ? "active" : ""}" data-go="${id}">${svg(n.icon)}<span>${n.short || n.label}</span>${dot}</button>`;
  }).join("");

  const me = state.me && state.me.user;
  if (me) {
    const av = avatarHtml(me, "avatar-sm");
    document.getElementById("side-user").innerHTML =
      `${av}<div><b>${esc(me.name)}</b><small>${me.username ? "@" + esc(me.username) : "Вайбометр"}</small></div>`;
    document.getElementById("top-avatar").outerHTML = `<div id="top-avatar" data-go="profile">${av}</div>`;
    document.getElementById("top-streak").innerHTML = `🔥 ${days(state.me.stats.streak_days)}`;
  }
}

document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-go]");
  if (el) { haptic("light"); go(el.dataset.go); }
});

function avatarHtml(p, cls = "") {
  const url = state.photos[p.id];
  const style = url ? ` style="background-image:url('${url}')"` : "";
  return `<div class="avatar ${cls}"${style}>${url ? "" : esc((p.name || "?")[0])}</div>`;
}

async function loadPhoto(id) {
  if (state.photos[id] !== undefined) return state.photos[id];
  state.photos[id] = await api.photo(id).catch(() => null);
  return state.photos[id];
}

// =========================================================
// Экраны
// =========================================================
const view = () => document.getElementById("view");

const screens = {
  home() {
    const { user, stats, level, achievements } = state.me;
    const next = nextGoal(achievements);
    const inc = state.vibes.incoming.length;
    const mut = state.vibes.mutual;
    const acts = [];
    if (inc) acts.push(["🩷", `Тебя оценили: ${inc}`, "Загляни в «Мои вайбы»", "vibes"]);
    mut.slice(0, 2).forEach((m) => acts.push(["💞", "Взаимный вайб", `С ${esc(m.name)}, напиши первым`, "vibes"]));
    if (!acts.length) acts.push(["⚡", "Пока тихо", "Полистай анкеты, вайб сам себя не найдёт", "search"]);

    return `
      <div class="hello">
        <h1>Привет, ${esc(user.name)} <span>👋</span></h1>
        <p class="sub">Отличный день, чтобы найти кого-то на одной волне</p>
      </div>
      <div class="tiles">
        <button class="tile pink" data-go="search"><div class="ico">${svg("heart")}</div><b>Поиск вайба</b><small>Новые знакомства</small></button>
        <button class="tile violet" data-go="vibes"><div class="ico">${svg("heart")}</div><b>Мои вайбы</b><small>${inc ? `${inc} ${plural(inc, "новый", "новых", "новых")}` : "Взаимные лайки"}</small></button>
        <button class="tile blue" data-go="games"><div class="ico">${svg("game")}</div><b>Игры</b><small>«Что выберешь?»</small></button>
        <button class="tile gold" data-go="profile"><div class="ico">${svg("user")}</div><b>Профиль</b><small>Твоя анкета</small></button>
      </div>
      <div class="grid mt" style="grid-template-columns:repeat(auto-fit,minmax(260px,1fr))">
        <div class="card">
          <h2>Твой прогресс</h2>
          ${levelRow(level)}
        </div>
        <div class="card" data-go="fame" style="cursor:pointer">
          <h2>Ближайшее достижение</h2>
          ${next ? goalRow(next) : `<p class="muted">Всё открыто. Ты легенда 👑</p>`}
        </div>
      </div>
      <div class="card mt">
        <div class="row between"><h2>Недавняя активность</h2></div>
        <div class="activity">
          ${acts.map(([ic, t, s, to]) => `<button class="act" data-go="${to}" style="text-align:left"><div class="ai">${ic}</div><div><b>${t}</b><div class="small muted">${s}</div></div></button>`).join("")}
        </div>
      </div>
      <div class="grid grid-2 mt">
        <div class="stat-tile"><div class="si">🔥</div><div><b>${days(stats.streak_days)}</b><small>серия · рекорд ${stats.best_streak}</small></div></div>
        <div class="stat-tile"><div class="si">💞</div><div><b>${stats.mutual_likes}</b><small>${plural(stats.mutual_likes, "взаимный вайб", "взаимных вайба", "взаимных вайбов")}</small></div></div>
      </div>`;
  },

  search() {
    return `
      <h1>Поиск вайба</h1>
      <p class="sub">Люди, которые могут тебе подойти</p>
      <div class="seg" id="gender-seg">
        ${[["all", "Все"], ["female", "Девушки"], ["male", "Парни"]].map(([v, l]) =>
          `<button data-sg="${v}" class="${state.me.user.search_gender === v ? "on" : ""}">${l}</button>`).join("")}
      </div>
      <div class="deck" id="deck"><div class="empty"><div class="big">✨</div><p class="muted">Ищем вайб…</p></div></div>
      <div class="actions" id="deck-actions">
        <button class="btn btn-ghost" id="btn-skip">${svg("x")} Мимо</button>
        <button class="btn btn-pink" id="btn-like">${svg("heart")} Вайб</button>
      </div>
      <div class="actions-mini">
        <button id="btn-question">${svg("chat")} Вопрос</button>
        <button id="btn-report">${svg("flag")} Пожаловаться</button>
      </div>`;
  },

  vibes() {
    const { incoming, mutual } = state.vibes;
    const card = (p, kind) => `
      <div class="person">
        ${avatarHtml(p, kind === "mutual" ? "pink" : "")}
        <div class="pi"><b>${esc(p.name)}, ${p.age}</b><small>📍 ${esc(p.city || "")}</small></div>
        ${kind === "mutual"
          ? `<button class="btn btn-pink btn-sm" data-write="${p.id}">Написать</button>`
          : `<button class="btn btn-ghost btn-sm" data-inc-skip="${p.id}">Мимо</button><button class="btn btn-pink btn-sm" data-inc-like="${p.id}">Вайб</button>`}
      </div>`;
    return `
      <h1>Мои вайбы</h1>
      <p class="sub">Кто тебя выбрал и с кем взаимно</p>
      <h2>💌 Тебя оценили</h2>
      <div class="list">${incoming.length ? incoming.map((p) => card(p, "in")).join("") : `<p class="muted">Пока никого. Лайкай смелее, и тебя заметят</p>`}</div>
      <h2 class="mt-l">💞 Взаимные</h2>
      <div class="list">${mutual.length ? mutual.map((p) => card(p, "mutual")).join("") : `<p class="muted">Здесь появятся люди, с которыми вайб совпал</p>`}</div>`;
  },

  games() {
    return `
      <h1>Игры</h1>
      <p class="sub">Проверь, насколько вы на одной волне</p>
      <div class="list">
        <div class="game">
          <div class="gi">🍭</div>
          <div class="gt"><b>Что выберешь?</b><br><small>5 вопросов «а или б» с человеком на одной волне, в конце процент совпадения</small></div>
          <button class="btn btn-violet btn-sm" id="play-game">Играть</button>
        </div>
        <div class="game soon"><div class="gi">🎯</div><div class="gt"><b>Викторина</b><br><small>Скоро</small></div></div>
        <div class="game soon"><div class="gi">🔥</div><div class="gt"><b>Правда или действие</b><br><small>Скоро</small></div></div>
      </div>`;
  },

  profile() {
    const { user, stats, level, achievements } = state.me;
    const photo = state.photos[user.id];
    const next = nextGoal(achievements);
    return `
      <div class="card">
        <div class="profile-head">
          <div class="profile-photo"${photo ? ` style="background-image:url('${photo}')"` : ""}>${photo ? "" : esc(user.name[0])}</div>
          <div style="min-width:0">
            <h1 style="margin:0">${esc(user.name)} <span style="font-size:20px">👑</span></h1>
            <div class="muted">${user.age} · 📍 ${esc(user.city)}</div>
            <p style="margin:8px 0 0;color:#d5cdef">${esc(user.about || "")}</p>
          </div>
        </div>
        <div class="chips mt">${user.interests.map((t) => `<span class="chip">${esc(t)}</span>`).join("")}</div>
        <div class="mt">${levelRow(level)}</div>
      </div>
      <div class="grid grid-4 mt">
        <div class="stat-tile"><div class="si">🩷</div><div><b>${stats.likes_sent}</b><small>лайков</small></div></div>
        <div class="stat-tile"><div class="si">💞</div><div><b>${stats.mutual_likes}</b><small>взаимных</small></div></div>
        <div class="stat-tile"><div class="si">🎮</div><div><b>${stats.games}</b><small>игр</small></div></div>
        <div class="stat-tile"><div class="si">🔥</div><div><b>${stats.streak_days}</b><small>серия</small></div></div>
      </div>
      ${next ? `<div class="card mt" data-go="fame" style="cursor:pointer"><h2>Ближайшая цель</h2>${goalRow(next)}</div>` : ""}
      <div class="card mt">
        <div class="row between"><h2 style="margin:0">Твои достижения</h2><button class="btn btn-ghost btn-sm" data-go="fame">Все</button></div>
        <div class="ach-grid mt">${achievements.slice(0, 5).map(achHtml).join("")}</div>
      </div>
      <button class="btn btn-ghost btn-block mt" id="edit-profile">✏️ Изменить анкету в боте</button>`;
  },

  fame() {
    const list = state.me.achievements;
    const f = state.fameFilter || "all";
    const shown = list.filter((a) => f === "all" || (f === "open" ? a.done : !a.done));
    const done = list.filter((a) => a.done).length;
    return `
      <h1>Зал славы</h1>
      <p class="sub">Открыто ${done} из ${list.length}. Твои достижения и новые цели</p>
      <div class="seg">
        ${[["all", "Все"], ["open", "Открытые"], ["locked", "Впереди"]].map(([v, l]) =>
          `<button data-fame="${v}" class="${f === v ? "on" : ""}">${l}</button>`).join("")}
      </div>
      <div class="card"><div class="ach-grid">${shown.map(achHtml).join("") || `<p class="muted">Пусто</p>`}</div></div>`;
  },

  stats() {
    const { stats, level } = state.me;
    const pct = Math.round((level.done / level.total) * 100);
    const C = 2 * Math.PI * 64;
    const t = (ic, v, l) => `<div class="stat-tile"><div class="si">${ic}</div><div><b>${v}</b><small>${l}</small></div></div>`;
    return `
      <h1>Статистика</h1>
      <p class="sub">Твои успехи в цифрах</p>
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr))">
        <div class="card" style="text-align:center">
          <div class="ring">
            <svg viewBox="0 0 150 150"><circle cx="75" cy="75" r="64" stroke="rgba(255,255,255,.07)" stroke-width="10" fill="none"/>
              <circle cx="75" cy="75" r="64" stroke="url(#rg)" stroke-width="10" fill="none" stroke-linecap="round"
                stroke-dasharray="${C}" stroke-dashoffset="${C * (1 - pct / 100)}"/>
              <defs><linearGradient id="rg"><stop offset="0" stop-color="#9b5cff"/><stop offset="1" stop-color="#ff3d9a"/></linearGradient></defs></svg>
            <div class="rv"><div><b>${pct}%</b><small class="muted">прогресс</small></div></div>
          </div>
          <p class="muted small">${level.done} из ${level.total} достижений</p>
        </div>
        <div class="grid grid-2">
          ${t("🩷", stats.likes_sent, "лайков")}
          ${t("💌", stats.likes_received, "тебя выбрали")}
          ${t("💞", stats.mutual_likes, "взаимных")}
          ${t("🎮", stats.games, "игр")}
          ${t("❓", stats.questions_sent, "вопросов задано")}
          ${t("🔥", stats.best_streak, "рекорд серии")}
        </div>
      </div>`;
  },

  settings() {
    const item = (ic, t, s, id) => `<button class="set-item" id="${id}"><span style="font-size:22px">${ic}</span><span class="st"><b>${t}</b><small>${s}</small></span><span class="chev">${svg("chev")}</span></button>`;
    return `
      <h1>Настройки</h1>
      <p class="sub">Управляй своим аккаунтом</p>
      <div class="list">
        ${item("✏️", "Анкета", "Изменить имя, фото, интересы", "set-edit")}
        ${item("🎯", "Кого искать", "Девушки, парни или все", "set-search")}
        ${item("🚫", "Заблокированные", "Список в боте", "set-blocked")}
        ${item("🔒", "Конфиденциальность", "Фото видно только при взаимном вайбе", "set-privacy")}
      </div>`;
  },
};

function levelRow(level) {
  const pct = Math.round((level.done / level.total) * 100);
  return `
    <div class="row">
      <div class="level-badge">👑</div>
      <div style="flex:1">
        <div class="row between"><b>Уровень ${level.n} · ${level.name}</b><span class="small muted">${level.done} из ${level.total}</span></div>
        <div class="bar mt" style="margin-top:8px"><i style="width:${pct}%"></i></div>
      </div>
    </div>`;
}

function nextGoal(list) {
  return list.filter((a) => !a.done).sort((a, b) => b.value / b.goal - a.value / a.goal)[0];
}

function goalRow(a) {
  const pct = Math.min(100, Math.round((a.value / a.goal) * 100));
  return `
    <div class="row">
      <div class="lock-badge">${a.icon}</div>
      <div style="flex:1">
        <div class="row between"><b>${esc(a.name)}</b><span class="small muted">${a.value} / ${a.goal}</span></div>
        <div class="small muted">${esc(a.hint)}</div>
        <div class="bar" style="margin-top:8px"><i style="width:${pct}%"></i></div>
      </div>
    </div>`;
}

function achHtml(a) {
  const pct = Math.min(100, Math.round((a.value / a.goal) * 100));
  return `
    <div class="ach ${a.done ? "done" : "locked"}">
      <div class="medal">${a.done ? a.icon : "🔒"}</div>
      <b>${esc(a.name)}</b>
      <small>${a.done ? "Открыто" : `${a.value} из ${a.goal}`}</small>
      ${a.done ? "" : `<div class="bar"><i style="width:${pct}%"></i></div>`}
    </div>`;
}

// =========================================================
// Поиск: колода и свайп
// =========================================================
async function loadCandidate() {
  const deck = document.getElementById("deck");
  if (!deck) return;
  try {
    const { candidate } = await api.next();
    state.candidate = candidate;
  } catch (e) {
    deck.innerHTML = errorHtml(e);
    return;
  }
  const c = state.candidate;
  document.getElementById("deck-actions").style.visibility = c ? "visible" : "hidden";
  document.querySelector(".actions-mini").style.visibility = c ? "visible" : "hidden";
  if (!c) {
    deck.innerHTML = `<div class="empty"><div class="big">🌙</div><h2>Анкеты закончились</h2><p class="muted">Загляни попозже, люди подтягиваются каждый день</p></div>`;
    return;
  }
  deck.innerHTML = `<div class="pcard back"></div>${cardHtml(c)}`;
  bindSwipe(deck.querySelector(".pcard:not(.back)"));
}

function hue(id) {
  const palettes = [["#b04cff", "#ff3d9a"], ["#6d5bff", "#c13cff"], ["#ff3d9a", "#ff8a3d"], ["#3d7bff", "#b04cff"]];
  return palettes[id % palettes.length];
}

function cardHtml(c) {
  const [a1, a2] = hue(c.id);
  const common = new Set((c.common || []).map((x) => x.toLowerCase()));
  const tags = (c.interests || []).map((t) =>
    `<span class="chip ${common.has(t.toLowerCase()) ? "common" : ""}">${esc(t)}</span>`).join("");
  return `
    <div class="pcard" style="--a1:${a1};--a2:${a2}">
      <div class="stamp like">ВАЙБ</div>
      <div class="stamp skip">МИМО</div>
      <div class="aura">
        <div class="vibe-pill">🔥 ${c.vibe}% вайба</div>
        <div class="silhouette">${esc((c.name || "?")[0])}</div>
        <div class="locked-note">${svg("lock").replace("<svg", '<svg width="14" height="14"')} Фото откроется после взаимного вайба</div>
      </div>
      <div class="info">
        <div class="name">${esc(c.name)}, ${c.age}</div>
        <div class="city">📍 ${esc(c.city || "")}</div>
        <div class="chips">${tags}</div>
        ${c.about ? `<p class="about">${esc(c.about)}</p>` : ""}
      </div>
    </div>`;
}

function bindSwipe(card) {
  let x0 = 0, y0 = 0, dx = 0, dragging = false;
  const like = card.querySelector(".stamp.like"), skip = card.querySelector(".stamp.skip");

  card.addEventListener("pointerdown", (e) => {
    dragging = true; x0 = e.clientX; y0 = e.clientY; dx = 0;
    card.setPointerCapture(e.pointerId);
    card.style.transition = "none";
  });
  card.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    dx = e.clientX - x0;
    const dy = (e.clientY - y0) * 0.2;
    card.style.transform = `translate(${dx}px, ${dy}px) rotate(${dx / 18}deg)`;
    like.style.opacity = Math.max(0, Math.min(1, dx / 90));
    skip.style.opacity = Math.max(0, Math.min(1, -dx / 90));
  });
  const end = () => {
    if (!dragging) return;
    dragging = false;
    if (dx > 100) decide("like");
    else if (dx < -100) decide("skip");
    else {
      card.style.transition = "transform .25s ease";
      card.style.transform = "";
      like.style.opacity = skip.style.opacity = 0;
    }
  };
  card.addEventListener("pointerup", end);
  card.addEventListener("pointercancel", end);
}

let deciding = false;
async function decide(action) {
  const c = state.candidate;
  const card = document.querySelector("#deck .pcard:not(.back)");
  if (!c || !card || deciding) return;
  deciding = true;
  haptic(action === "like" ? "medium" : "light");

  const dir = action === "like" ? 1 : -1;
  card.style.transition = "transform .35s ease, opacity .35s ease";
  card.style.transform = `translate(${dir * 600}px, -30px) rotate(${dir * 24}deg)`;
  card.style.opacity = "0";
  card.querySelector(action === "like" ? ".stamp.like" : ".stamp.skip").style.opacity = 1;

  try {
    const res = await api.vibe(c.id, action);
    if (res.mutual) { haptic("success"); showMatch(res.match); refreshSoft(); }
  } catch (e) {
    toast(e.code === "banned" ? "Аккаунт заблокирован" : "Не получилось, попробуй ещё раз");
  }
  setTimeout(() => { deciding = false; loadCandidate(); }, 300);
}

// =========================================================
// Экран взаимности
// =========================================================
async function showMatch(m) {
  const me = state.me.user;
  const ov = document.getElementById("overlay");
  const hearts = Array.from({ length: 14 }, () =>
    `<span class="float-heart" style="left:${Math.random() * 100}%;top:${20 + Math.random() * 70}%;font-size:${10 + Math.random() * 18}px;animation-duration:${3 + Math.random() * 4}s;animation-delay:${-Math.random() * 5}s">♥</span>`).join("");
  ov.innerHTML = `
    ${hearts}
    <h1 class="match-title">Взаимный вайб!</h1>
    <p class="muted" style="margin:6px 0 0">Вы понравились друг другу</p>
    <div class="match-pair">
      <div class="who" id="who-me">${avatarHtml(me, "avatar-xl")}<b>${esc(me.name)}</b><small>${me.age} лет</small></div>
      <div class="match-heart">💗</div>
      <div class="who" id="who-them">${avatarHtml(m, "avatar-xl pink")}<b>${esc(m.name)}</b><small>${m.age} лет</small></div>
    </div>
    <p class="small muted" style="max-width:300px">Фото открылось. Бот тоже прислал контакт в чат</p>
    <div class="match-actions">
      <button class="btn btn-pink" id="match-write">${svg("chat")} Написать</button>
      <button class="btn btn-ghost" id="match-close">Искать дальше</button>
    </div>`;
  ov.classList.remove("hidden");
  document.getElementById("match-write").onclick = () => writeTo(m);
  document.getElementById("match-close").onclick = () => ov.classList.add("hidden");

  // фото подгружаем уже после показа экрана
  for (const [p, box] of [[me, "who-me"], [m, "who-them"]]) {
    if (p.has_photo === false) continue;
    const url = await loadPhoto(p.id);
    const el = document.querySelector(`#${box} .avatar`);
    if (url && el) { el.style.backgroundImage = `url('${url}')`; el.textContent = ""; }
  }
}

function writeTo(p) {
  haptic("light");
  if (DEMO) { toast(`Откроется чат с ${p.name}`); return; }
  if (p.username) tg.openTelegramLink(`https://t.me/${p.username}`);
  else { toast("Ссылка на профиль у тебя в чате с ботом"); setTimeout(() => tg.close(), 1200); }
}

function toBot(hint) {
  if (DEMO) { toast(hint); return; }
  toast(hint);
  setTimeout(() => tg.close(), 1200);
}

// =========================================================
// Шторка: вопрос и жалоба
// =========================================================
const REPORT_REASONS = [
  ["fake", "Фейк или спам"],
  ["rude", "Оскорбления"],
  ["nsfw", "Неприемлемый контент"],
  ["minor", "Похоже, младше 18"],
  ["other", "Другое"],
];
const QUESTION_MAX = 500;

function openSheet(html) {
  const sheet = document.getElementById("sheet");
  sheet.innerHTML = `<div class="sheet-backdrop" data-close></div><div class="sheet-panel"><div class="sheet-grip"></div>${html}</div>`;
  sheet.classList.remove("hidden");
  sheet.querySelectorAll("[data-close]").forEach((el) => el.onclick = closeSheet);
  return sheet;
}

function closeSheet() {
  document.getElementById("sheet").classList.add("hidden");
}

function openQuestion(p) {
  const sheet = openSheet(`
    <h2 class="sheet-title">Задай вопрос · ${esc(p.name)}</h2>
    <p class="muted small" style="margin:0 0 12px">Анонимно: ${esc(p.name)} не узнает, кто спросил</p>
    <textarea id="q-text" class="field" rows="4" maxlength="${QUESTION_MAX}" placeholder="Например: какой фильм пересматриваешь чаще всего?"></textarea>
    <div class="row between small muted" style="margin:6px 2px 14px"><span>Ответ придёт в чат с ботом</span><span id="q-count">0 / ${QUESTION_MAX}</span></div>
    <button class="btn btn-violet btn-block" id="q-send" disabled>${svg("chat")} Отправить</button>`);
  const area = sheet.querySelector("#q-text"), send = sheet.querySelector("#q-send");
  area.oninput = () => {
    const n = area.value.trim().length;
    sheet.querySelector("#q-count").textContent = `${area.value.length} / ${QUESTION_MAX}`;
    send.disabled = n === 0;
  };
  setTimeout(() => area.focus(), 250);
  send.onclick = async () => {
    send.disabled = true;
    try {
      await api.question(p.id, area.value.trim());
      haptic("success");
      closeSheet();
      toast("Вопрос улетел 💬");
    } catch (e) {
      send.disabled = false;
      toast(e.code === "not_delivered" ? "Не получилось доставить, человек закрыл бота" : "Не получилось отправить, попробуй ещё раз");
    }
  };
}

function openReport(p) {
  const sheet = openSheet(`
    <h2 class="sheet-title">Пожаловаться · ${esc(p.name)}</h2>
    <p class="muted small" style="margin:0 0 12px">Анкета сразу пропадёт из твоей выдачи, модератор проверит</p>
    <div class="list">${REPORT_REASONS.map(([code, label]) =>
      `<button class="set-item" data-reason="${code}"><span class="st"><b>${label}</b></span><span class="chev">${svg("chev")}</span></button>`).join("")}</div>
    <button class="btn btn-ghost btn-block mt" data-close>Отмена</button>`);
  sheet.querySelectorAll("[data-close]").forEach((el) => el.onclick = closeSheet);
  sheet.querySelectorAll("[data-reason]").forEach((b) => b.onclick = async () => {
    try {
      await api.report(p.id, b.dataset.reason);
      haptic("success");
      closeSheet();
      toast("Жалоба отправлена, спасибо");
      dismissCard();
    } catch (_) {
      toast("Не получилось отправить, попробуй ещё раз");
    }
  });
}

// Убрать карточку без лайка и скипа (после жалобы)
function dismissCard() {
  const card = document.querySelector("#deck .pcard:not(.back)");
  if (card) {
    card.style.transition = "transform .3s ease, opacity .3s ease";
    card.style.transform = "translateY(40px) scale(.9)";
    card.style.opacity = "0";
  }
  setTimeout(loadCandidate, 300);
}

// =========================================================
// Рендер и обработчики экранов
// =========================================================
function errorHtml(e) {
  const banned = e && e.code === "banned";
  const noProfile = e && e.code === "no_profile";
  return `<div class="empty"><div class="big">${banned ? "🚫" : noProfile ? "📝" : "📡"}</div>
    <h2>${banned ? "Аккаунт заблокирован" : noProfile ? "Сначала анкета" : "Нет связи"}</h2>
    <p class="muted">${banned ? "За нарушение правил Вайбометра" : noProfile ? "Заполни анкету в боте: напиши /start" : "Не получилось загрузить, попробуй ещё раз"}</p>
    ${banned ? "" : `<button class="btn btn-violet mt" onclick="${noProfile ? "tg && tg.close()" : "boot()"}">${noProfile ? "Открыть бота" : "Повторить"}</button>`}</div>`;
}

async function refreshSoft() {
  try {
    const [me, vibes] = await Promise.all([api.me(), api.vibes()]);
    state.me = me; state.vibes = vibes;
    renderNav();
  } catch (_) {}
}

function render() {
  if (!state.me) return;
  let r = route();
  if (!screens[r]) r = "home";
  view().innerHTML = screens[r]();
  view().style.animation = "none"; void view().offsetWidth; view().style.animation = "";
  window.scrollTo(0, 0);
  renderNav();

  if (tg && tg.BackButton) {
    if (r === "home") tg.BackButton.hide(); else tg.BackButton.show();
  }

  if (r === "search") {
    loadCandidate();
    document.getElementById("btn-like").onclick = () => decide("like");
    document.getElementById("btn-skip").onclick = () => decide("skip");
    document.getElementById("btn-question").onclick = () => state.candidate && openQuestion(state.candidate);
    document.getElementById("btn-report").onclick = () => state.candidate && openReport(state.candidate);
    document.querySelectorAll("[data-sg]").forEach((b) => b.onclick = async () => {
      haptic("light");
      await api.setSearch(b.dataset.sg).catch(() => toast("Не получилось сохранить"));
      state.me.user.search_gender = b.dataset.sg;
      render();
    });
  }
  if (r === "vibes") {
    document.querySelectorAll("[data-write]").forEach((b) => b.onclick = () =>
      writeTo(state.vibes.mutual.find((p) => String(p.id) === b.dataset.write)));
    document.querySelectorAll("[data-inc-like],[data-inc-skip]").forEach((b) => b.onclick = async () => {
      const like = !!b.dataset.incLike;
      const id = Number(b.dataset.incLike || b.dataset.incSkip);
      try {
        const res = await api.vibe(id, like ? "like" : "skip");
        if (res.mutual) showMatch(res.match);
        await refreshSoft(); render();
      } catch (_) { toast("Не получилось, попробуй ещё раз"); }
    });
    state.vibes.mutual.forEach((p) => p.has_photo !== false && loadPhoto(p.id).then((url) => {
      const el = document.querySelector(`[data-write="${p.id}"]`);
      const av = el && el.closest(".person").querySelector(".avatar");
      if (url && av) { av.style.backgroundImage = `url('${url}')`; av.textContent = ""; }
    }));
  }
  if (r === "fame") {
    document.querySelectorAll("[data-fame]").forEach((b) => b.onclick = () => { state.fameFilter = b.dataset.fame; render(); });
  }
  if (r === "games") {
    document.getElementById("play-game").onclick = () => toBot("Игра запускается в чате с ботом: «🍭 Игры»");
  }
  if (r === "profile") {
    document.getElementById("edit-profile").onclick = () => toBot("Анкету меняем в боте: «⚙️ Настройки» → «Изменить анкету»");
  }
  if (r === "settings") {
    document.getElementById("set-edit").onclick = () => toBot("Анкету меняем в боте: «⚙️ Настройки» → «Изменить анкету»");
    document.getElementById("set-search").onclick = () => go("search");
    document.getElementById("set-blocked").onclick = () => toBot("Список заблокированных — в боте: «⚙️ Настройки»");
    document.getElementById("set-privacy").onclick = () => toast("Фото видят только те, с кем у тебя взаимный вайб");
  }
}

if (tg && tg.BackButton) tg.BackButton.onClick(() => {
  const ov = document.getElementById("overlay");
  if (!ov.classList.contains("hidden")) { ov.classList.add("hidden"); return; }
  if (!document.getElementById("sheet").classList.contains("hidden")) { closeSheet(); return; }
  history.length > 1 ? history.back() : go("home");
});

async function boot() {
  if (DEMO) document.body.insertAdjacentHTML("beforeend", '<div class="demo-badge">демо-режим</div>');
  view().innerHTML = `<div class="empty"><div class="big">✨</div><p class="muted">Загружаем вайб…</p></div>`;
  try {
    const [me, vibes] = await Promise.all([api.me(), api.vibes()]);
    state.me = me; state.vibes = vibes;
    if (me.user.has_photo !== false) loadPhoto(me.user.id).then(() => { renderNav(); if (route() === "profile") render(); });
    render();
  } catch (e) {
    view().innerHTML = errorHtml(e);
  }
}

boot();
