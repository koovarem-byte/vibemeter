/* =========================================================
   ВАЙБОМЕТР · Mini App
   Без Telegram (пустой initData) работает в демо-режиме на моках.
   ========================================================= */
"use strict";

const tg = window.Telegram && window.Telegram.WebApp;
const DEMO = !tg || !tg.initData;

if (tg) {
  tg.ready();
  tg.expand();
  try { tg.setHeaderColor("#07060d"); tg.setBackgroundColor("#07060d"); } catch (_) {}
  // свайп карточки вниз не должен закрывать приложение
  try { tg.disableVerticalSwipes && tg.disableVerticalSwipes(); } catch (_) {}
}

// =========================================================
// Мелочи
// =========================================================
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

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

const store = {
  get(k) { try { return localStorage.getItem(k); } catch (_) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (_) {} },
};

function haptic(type) {
  try {
    if (!tg || !tg.HapticFeedback) return;
    if (type === "success" || type === "error" || type === "warning") tg.HapticFeedback.notificationOccurred(type);
    else if (type === "select") tg.HapticFeedback.selectionChanged();
    else tg.HapticFeedback.impactOccurred(type || "light");
  } catch (_) {}
}

function toast(text) {
  const t = $("#toast");
  t.textContent = text;
  t.classList.remove("hidden");
  t.style.animation = "none"; void t.offsetWidth; t.style.animation = "";
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.add("hidden"), 2400);
}

// =========================================================
// Иконки
// =========================================================
const I = {
  home: '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
  heart: '<path d="M12 20s-7-4.4-9.2-8.6C1.2 8.3 3 4.5 6.6 4.5c2.1 0 3.4 1.2 4.4 2.6 1-1.4 2.3-2.6 4.4-2.6 3.6 0 5.4 3.8 3.8 6.9C19 15.6 12 20 12 20z"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.2-4 4.3-6 8-6s6.8 2 8 6"/>',
  game: '<rect x="2" y="7" width="20" height="11" rx="5"/><path d="M7 11v3M5.5 12.5h3M15 12h.01M18 13.5h.01"/>',
  crown: '<path d="M3 8l4.5 4L12 5l4.5 7L21 8l-2 11H5z"/>',
  chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
  chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/>',
  flag: '<path d="M5 21V4h11l-1.5 4L16 12H5"/>',
  chev: '<path d="M9 6l6 6-6 6"/>',
  more: '<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>',
  undo: '<path d="M9 14L4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-3"/>',
  camera: '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
  share: '<circle cx="18" cy="5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="19" r="2.5"/><path d="M8.2 10.8l7.6-4.4M8.2 13.2l7.6 4.4"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  fire: '<path d="M12 3c1 3 4 4.5 4 8.5a4 4 0 0 1-8 0c0-1.5.6-2.5 1.5-3.5C9.5 9.5 11 8 12 3z"/><path d="M10.5 16.5a1.6 1.6 0 0 0 3 0c0-1-.8-1.6-1.5-2.4-.7.8-1.5 1.4-1.5 2.4z"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
  help: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 .9-1 1.7M12 17h.01"/>',
  ban: '<circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/>',
  spark: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z"/>',
};
const svg = (name, cls = "") =>
  `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${I[name]}</svg>`;

// =========================================================
// Бренд: знак-шкала и шкала вайба
// =========================================================
let uid = 0;

function brandMark() {
  const id = `bm${++uid}`;
  return `<svg class="brand-mark" viewBox="0 0 64 40" fill="none">
    <defs><linearGradient id="${id}" x1="0" x2="1"><stop offset="0" stop-color="#9b5cff"/><stop offset="1" stop-color="#ff3d9a"/></linearGradient></defs>
    <path d="M7 35a25 25 0 0 1 50 0" stroke="url(#${id})" stroke-width="5" stroke-linecap="round"/>
    <path d="M32 35L47 17" stroke="#fff" stroke-width="3" stroke-linecap="round"/>
    <path d="M32 39.5s-5-3-6.3-5.7c-1-2.1.2-4.6 2.6-4.6 1.4 0 2.3.8 3.7 2 1.4-1.2 2.3-2 3.7-2 2.4 0 3.6 2.5 2.6 4.6C37 36.5 32 39.5 32 39.5z" fill="#ff3d9a"/>
  </svg>`;
}

function brandHtml() {
  return `${brandMark()}<span class="wordmark">Вайбометр</span>`;
}

function vibeWord(p) {
  if (p >= 85) return "вайб на максимум";
  if (p >= 70) return "сильный вайб";
  if (p >= 55) return "хороший вайб";
  return "есть контакт";
}

// Полукруглая шкала: стрелка доезжает до значения после показа
function gauge(pct, size = 84, cap = "вайб") {
  const id = `gg${++uid}`;
  const sw = Math.max(5, size * 0.08);
  const r = size / 2 - sw;
  const cx = size / 2, cy = r + sw;
  const h = cy + sw * 0.6;
  const len = Math.PI * r;
  const ticks = Array.from({ length: 11 }, (_, i) => {
    const a = Math.PI - (Math.PI * i) / 10;
    const r1 = r - sw * 1.3, r2 = r - sw * (i % 5 === 0 ? 2.4 : 1.9);
    return `<line x1="${cx + r1 * Math.cos(a)}" y1="${cy - r1 * Math.sin(a)}" x2="${cx + r2 * Math.cos(a)}" y2="${cy - r2 * Math.sin(a)}" stroke="rgba(196,140,255,.45)" stroke-width="1.2"/>`;
  }).join("");
  const fs = Math.max(13, size * 0.2);
  return `<div class="gauge" data-pct="${pct}" style="width:${size}px">
    <svg width="${size}" height="${h}" viewBox="0 0 ${size} ${h}" fill="none">
      <defs><linearGradient id="${id}" x1="0" x2="1"><stop offset="0" stop-color="#9b5cff"/><stop offset="1" stop-color="#ff3d9a"/></linearGradient></defs>
      <path d="M${cx - r} ${cy}a${r} ${r} 0 0 1 ${2 * r} 0" stroke="rgba(255,255,255,.08)" stroke-width="${sw}" stroke-linecap="round"/>
      <path class="g-arc" d="M${cx - r} ${cy}a${r} ${r} 0 0 1 ${2 * r} 0" stroke="url(#${id})" stroke-width="${sw}" stroke-linecap="round"
        stroke-dasharray="0 ${len}" data-len="${len}" style="transition:stroke-dasharray 1.1s cubic-bezier(.2,.9,.25,1);filter:drop-shadow(0 0 ${sw * 0.6}px rgba(255,61,154,.6))"/>
      ${ticks}
      <g class="needle" style="transform-origin:${cx}px ${cy}px;transform:rotate(-90deg)">
        <line x1="${cx}" y1="${cy}" x2="${cx}" y2="${cy - r + sw * 1.6}" stroke="#fff" stroke-width="${Math.max(2, sw * 0.4)}" stroke-linecap="round" style="filter:drop-shadow(0 0 3px #fff)"/>
      </g>
      <circle cx="${cx}" cy="${cy}" r="${sw * 0.75}" fill="#ff3d9a" style="filter:drop-shadow(0 0 4px #ff3d9a)"/>
    </svg>
    <div class="g-val" style="position:static;margin-top:4px;font-size:${fs}px">${pct}%${cap ? `<span class="g-cap">${cap}</span>` : ""}</div>
  </div>`;
}

function animateGauges(root = document) {
  requestAnimationFrame(() => requestAnimationFrame(() => {
    $$(".gauge", root).forEach((g) => {
      if (g.dataset.done) return;
      g.dataset.done = "1";
      const p = Math.max(0, Math.min(100, Number(g.dataset.pct) || 0)) / 100;
      const arc = $(".g-arc", g), len = Number(arc.dataset.len);
      arc.style.strokeDasharray = `${len * p} ${len}`;
      $(".needle", g).style.transform = `rotate(${-90 + 180 * p}deg)`;
    });
  }));
}

// =========================================================
// API
// =========================================================
const api = DEMO ? makeDemoApi() : {
  async call(path, body) {
    let res;
    try {
      res = await fetch(`api/${path}`, {
        method: body ? "POST" : "GET",
        headers: { "X-Init-Data": tg.initData, "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      });
    } catch (_) {
      throw Object.assign(new Error("network"), { code: "network" });
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.error || res.status), { code: data.error, status: res.status });
    return data;
  },
  me() { return this.call("me"); },
  next() { return this.call("next"); },
  vibe(id, action) { return this.call("vibe", { id, action }); },
  undo(id) { return this.call("undo", { id }); },
  vibes() { return this.call("vibes"); },
  saveProfile(data) { return this.call("profile", data); },
  question(id, text) { return this.call("question", { id, text }); },
  report(id, reason) { return this.call("report", { id, reason }); },
  daily(answer) { return this.call("daily", { answer }); },
  async uploadPhoto(blob) {
    const fd = new FormData();
    fd.append("photo", blob, "photo.jpg");
    const res = await fetch("api/upload_photo", { method: "POST", headers: { "X-Init-Data": tg.initData }, body: fd });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.error), { code: data.error });
    return data;
  },
  async story(blob) {
    const fd = new FormData();
    fd.append("photo", blob, "vibe.png");
    const res = await fetch("api/story", { method: "POST", headers: { "X-Init-Data": tg.initData }, body: fd });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.error), { code: data.error });
    return data;
  },
  async shareCard(blob) {
    const fd = new FormData();
    fd.append("photo", blob, "vibe.png");
    const res = await fetch("api/share_card", { method: "POST", headers: { "X-Init-Data": tg.initData }, body: fd });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw Object.assign(new Error(data.error), { code: data.error });
    return data;
  },
  duoList() { return this.call("duo/list"); },
  duoStart(kind, id) { return this.call("duo/start", { kind, id }); },
  duoState(id) { return this.call(`duo/state?id=${id}`); },
  duoAct(id, body) { return this.call("duo/act", { id, ...body }); },
  gameState() { return this.call("game/state"); },
  gameJoin() { return this.call("game/join", {}); },
  gameLeave() { return this.call("game/leave", {}); },
  gameAnswer(game_id, index, answer) { return this.call("game/answer", { game_id, index, answer }); },
  async photo(id) {
    const res = await fetch(`api/photo/${id}`, { headers: { "X-Init-Data": tg.initData } });
    if (!res.ok) return null;
    return URL.createObjectURL(await res.blob());
  },
};

function makeDemoApi() {
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  const me = {
    id: 1, name: "Артемий", age: 19, city: "Псков", username: "demo",
    interests: ["баскетбол", "музыка", "бизнес", "технологии"],
    about: "Развиваюсь. Создаю. Ищу своих", gender: "male", search_gender: "female", has_photo: false,
  };
  const people = [
    { id: 11, name: "Анастасия", age: 19, city: "Псков", interests: ["музыка", "спорт", "кино"], about: "Люблю музыку, спорт и красивые закаты. Ищу того, с кем можно молчать и не скучать", vibe: 65, common: ["музыка"], same_city: true, likes_me: true },
    { id: 12, name: "Вика", age: 21, city: "Псков", interests: ["технологии", "путешествия", "кофе"], about: "Фронтенд днём, горы по выходным", vibe: 65, common: ["технологии"], same_city: true },
    { id: 13, name: "Полина", age: 20, city: "Санкт-Петербург", interests: ["книги", "театр"], about: "Читаю быстрее, чем пишу", vibe: 40, common: [], same_city: false },
    { id: 14, name: "Даша", age: 22, city: "Псков", interests: ["бизнес", "музыка", "баскетбол"], about: "Запускаю кофейню и хожу на баскет", vibe: 85, common: ["баскетбол", "бизнес", "музыка"], same_city: true, likes_me: true },
    { id: 16, name: "Лера", age: 19, city: "Великие Луки", interests: ["аниме", "игры", "музыка"], about: "Мемы, аниме и ночные прогулки", vibe: 50, common: ["музыка"], same_city: false },
  ];
  const stats = { streak_days: 3, best_streak: 3, likes_sent: 1, likes_received: 2, mutual_likes: 1, games: 1, questions_sent: 0, questions_received: 0, skips: 0, blocks: 0, referrals: 1 };
  const defs = [
    ["🩷", "Первый вайб", "первый лайк", "likes_sent", 1],
    ["💎", "Взаимность", "первый взаимный вайб", "mutual_likes", 1],
    ["🔥", "В огне", "серия 7 дней", "best_streak", 7],
    ["💘", "Сердцеед", "25 лайков", "likes_sent", 25],
    ["👑", "Легенда", "серия 30 дней", "best_streak", 30],
    ["🍭", "Душа компании", "10 игр", "games", 10],
    ["⚡", "Болтун", "10 вопросов", "questions_sent", 10],
    ["⭐", "Магнит", "тебя выбрали 25 раз", "likes_received", 25],
    ["🚀", "Лидер вайба", "3 друга по твоей ссылке", "referrals", 3],
  ];
  const dailyDemo = { text: "Утро или ночь?", a: "Утро", b: "Ночь", answer: null };
  people[0].daily = { q: "Утро или ночь?", label: "Ночь", match: false };
  let queue = people.slice();
  const skipped = new Map();
  const mutual = [{ id: 15, name: "Соня", age: 20, city: "Псков", interests: ["музыка"], about: "", username: "demo", has_photo: false }];

  const build = () => {
    const achievements = defs.map(([icon, name, hint, key, goal]) =>
      ({ icon, name, hint, value: Math.min(stats[key], goal), goal, done: stats[key] >= goal }));
    const done = achievements.filter((a) => a.done).length;
    return { bot_username: "vibemeter_bot", daily: dailyDemo, user: { ...me }, stats: { ...stats }, achievements, level: levelFor(done, achievements.length) };
  };

  return {
    async me() { await wait(200); return build(); },
    async next() { await wait(350); return { candidate: queue[0] || null }; },
    async vibe(id, action) {
      await wait(150);
      const p = queue.find((x) => x.id === id);
      queue = queue.filter((x) => x.id !== id);
      if (action === "skip") { stats.skips++; if (p) skipped.set(id, p); return { mutual: false }; }
      stats.likes_sent++;
      if (p && p.likes_me) {
        stats.mutual_likes++;
        const m = { ...p, username: "demo", has_photo: false, openers: ["Вижу, ты тоже про «музыка». Как давно этим увлекаешься?", "Мы из одного города (Псков)! Какое у тебя любимое место здесь?", "Привет! Утро или ночь, какой ты человек?"] };
        mutual.unshift(m);
        return { mutual: true, match: m };
      }
      return { mutual: false };
    },
    async undo(id) {
      await wait(150);
      const p = skipped.get(id);
      if (!p) throw Object.assign(new Error(), { code: "not_found" });
      skipped.delete(id); queue.unshift(p);
      return { candidate: p };
    },
    async vibes() { await wait(150); return { incoming: queue.filter((p) => p.likes_me), mutual }; },
    async saveProfile(data) {
      await wait(300);
      if (data.name !== undefined) me.name = data.name;
      if (data.city !== undefined) me.city = data.city;
      if (data.about !== undefined) me.about = data.about;
      if (data.interests !== undefined) me.interests = data.interests;
      if (data.search_gender !== undefined) me.search_gender = data.search_gender;
      return { ok: true };
    },
    async daily(answer) { await wait(150); dailyDemo.answer = answer; return { ok: true, saved: true }; },
    async question() { await wait(300); stats.questions_sent++; return { ok: true }; },
    async report(id) { await wait(200); queue = queue.filter((x) => x.id !== id); return { ok: true }; },
    async uploadPhoto() { await wait(600); return { ok: true }; },
    async shareCard() { await wait(500); return { ok: true }; },
    async photo() { return null; },
    ...makeDemoDuo(wait, mutual),
    ...makeDemoGame(wait, people),
  };
}

// Игры на двоих в демо: партнёр отвечает мгновенно, чтобы можно было пройти всё до конца
function makeDemoDuo(wait, mutual) {
  const demo = { games: [] };
  const partner = () => ({ ...mutual[0], vibe: 80 });
  const QUIZ = [["Утро или ночь?", "Утро", "Ночь"], ["Горы или море?", "Горы", "Море"], ["Кофе или чай?", "Кофе", "Чай"], ["Собака или кот?", "Собака", "Кот"], ["Лето или зима?", "Лето", "Зима"]];
  const mk = (kind) => ({
    id: demo.games.length + 1, kind, title: kind === "quiz" ? "Викторина вайба" : "Правда или действие", status: "active", partner: partner(),
    my_turn: true, mine: [], log: [],
    view: kind === "quiz"
      ? { kind, phase: "answer", index: 0, total: 5, i_am_author: true, question: { q: QUIZ[0][0], a: QUIZ[0][1], b: QUIZ[0][2] } }
      : { kind, phase: "choose", round: 0, rounds: 6, my_turn: true, log: [] },
  });
  const find = (id) => demo.games.find((g) => g.id === id);
  return {
    async duoList() { await wait(120); return { games: demo.games }; },
    async duoStart(kind) { await wait(200); const g = mk(kind); demo.games.unshift(g); return g; },
    async duoState(id) { await wait(100); return find(id); },
    async duoAct(id, body) {
      await wait(250);
      const g = find(id), v = g.view;
      if (g.kind === "quiz") {
        g.mine.push(body.answer);
        if (g.mine.length < 5) { const q = QUIZ[g.mine.length]; v.index = g.mine.length; v.question = { q: q[0], a: q[1], b: q[2] }; }
        else { v.phase = "done"; v.index = 5; v.matches = 4; v.percentage = 80; v.items = QUIZ.map((q, i) => ({ q: q[0], a: q[1], b: q[2], self: g.mine[i], guess: i === 2 ? (g.mine[i] === "a" ? "b" : "a") : g.mine[i] })); g.my_turn = false; g.status = "finished"; }
        return g;
      }
      if (body.action === "choose") { v.phase = "answer"; v.pick = body.pick; v.prompt = body.pick === "truth" ? "Какая песня у тебя на повторе последние дни?" : "Опиши свой идеальный вечер одним предложением без слова «фильм»"; }
      else { v.log.push({ mine: true, pick: v.pick, prompt: v.prompt, answer: body.text || null, score: "fire" }); v.round += 2; v.phase = v.round >= 6 ? "done" : "choose"; v.pick = null; v.prompt = null; if (v.phase === "done") { g.status = "finished"; g.my_turn = false; } }
      return g;
    },
  };
}

// Игра в демо: «соперник» находится через 2 секунды и отвечает так же быстро
function makeDemoGame(wait, people) {
  const Q = [
    ["🌊 Жить у моря", "🏔️ Жить в горах"],
    ["🌙 Не спать ночью", "☀️ Не спать днём"],
    ["💰 Много денег", "⏳ Много свободного времени"],
    ["🎬 Смотреть фильмы", "🎮 Играть в игры"],
    ["👥 Большая компания", "🤝 Несколько близких друзей"],
  ];
  const opp = people[0];
  let g = { state: "idle" }, since = 0, answers = [];
  const snap = () => {
    if (g.state === "waiting" && Date.now() - since > 2000) {
      g = { state: "playing", game_id: 1, opponent: opp, answered: 0, total: 5 };
    }
    if (g.state === "playing") {
      const i = answers.length;
      return { ...g, answered: i, question: { index: i, text: "Что выберешь?", a: Q[i][0], b: Q[i][1] } };
    }
    if (g.state === "waiting_opponent" && Date.now() - since > 2500) {
      const pct = [40, 60, 80, 100][Math.floor(Math.random() * 4)];
      g = { state: "finished", game_id: 1, opponent: opp, matches: pct / 20, total: 5, percentage: pct };
    }
    return g;
  };
  return {
    async gameState() { await wait(120); return snap(); },
    async gameJoin() { await wait(150); answers = []; g = { state: "waiting" }; since = Date.now(); return g; },
    async gameLeave() { g = { state: "idle" }; return g; },
    async gameAnswer(id, index, answer) {
      await wait(150);
      answers.push(answer);
      if (answers.length >= 5) { g = { state: "waiting_opponent", game_id: 1, opponent: opp, answered: 5, total: 5 }; since = Date.now(); }
      return snap();
    },
  };
}

// Та же лесенка, что ui.level на сервере (для демо)
function levelFor(done, total) {
  const steps = [[0, "Новичок"], [2, "В теме"], [4, "Вайбер"], [6, "Звезда"], [total, "Легенда"]];
  let n = 1, name = steps[0][1], next_at = steps[1][0];
  steps.forEach(([at, nm], i) => { if (done >= at) { n = i + 1; name = nm; next_at = steps[i + 1] ? steps[i + 1][0] : total; } });
  return { n, name, done, total, next_at };
}

// =========================================================
// Состояние и навигация
// =========================================================
const state = {
  me: null, vibes: { incoming: [], mutual: [] },
  candidate: null, lastSkip: null, photos: {},
  vibesTab: "in", fameFilter: "all",
};

const NAV = [
  { id: "home", label: "Главная", icon: "home", tab: true },
  { id: "search", label: "Поиск вайба", short: "Поиск", icon: "search", tab: true },
  { id: "vibes", label: "Мои вайбы", short: "Вайбы", icon: "heart", tab: true },
  { id: "games", label: "Игры", icon: "game", tab: true },
  { id: "profile", label: "Профиль", icon: "user", tab: true },
  { id: "fame", label: "Зал славы", icon: "crown" },
  { id: "stats", label: "Статистика", icon: "chart" },
  { id: "settings", label: "Настройки", icon: "gear" },
];

const route = () => (location.hash || "#home").slice(1).split("?")[0];
function go(id) { if (route() === id) render(); else location.hash = id; }

window.addEventListener("hashchange", () => {
  $("#overlay").classList.add("hidden");
  closeSheet();
  render();
});

document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-go]");
  if (el) { haptic("select"); go(el.dataset.go); }
});

function renderChrome() {
  const r = route();
  const tabR = r === "edit" ? "profile" : r;
  const incoming = state.vibes.incoming.length;
  const badge = (id) => (id === "vibes" && incoming ? `<span class="badge">${incoming}</span>` : "");

  $$(".brand").forEach((b) => { if (!b.innerHTML) b.innerHTML = brandHtml(); });
  $("#side-nav").innerHTML = NAV.map((n) =>
    `<button class="side-link ${tabR === n.id ? "active" : ""}" data-go="${n.id}">${svg(n.icon)}<span>${n.label}</span>${badge(n.id)}</button>`).join("");
  $("#tabbar").innerHTML = NAV.filter((n) => n.tab).map((n) =>
    `<button class="tab ${tabR === n.id ? "active" : ""}" data-go="${n.id}">${svg(n.icon)}<span>${n.short || n.label}</span>${badge(n.id)}</button>`).join("");

  const me = state.me.user;
  $("#topbar-right").innerHTML =
    `<span class="pill fire">🔥 ${state.me.stats.streak_days}</span>
     <button data-go="profile">${avatarHtml(me, "sm")}</button>`;
}

function avatarHtml(p, cls = "") {
  const url = state.photos[p.id];
  return url
    ? `<div class="avatar photo ${cls}" style="--img:url('${url}')"></div>`
    : `<div class="avatar ${cls}">${esc((p.name || "?")[0])}</div>`;
}

async function loadPhoto(id) {
  if (id in state.photos) return state.photos[id];
  state.photos[id] = null;
  state.photos[id] = await api.photo(id).catch(() => null);
  return state.photos[id];
}

// подставить фото во все аватары человека, когда оно загрузилось
function paintPhoto(id) {
  const url = state.photos[id];
  if (!url) return;
  $$(`[data-pid="${id}"]`).forEach((el) => {
    el.classList.add("photo");
    el.style.setProperty("--img", `url('${url}')`);
    el.textContent = "";
  });
}
function avatarFor(p, cls = "") {
  const url = state.photos[p.id];
  return `<div class="avatar ${url ? "photo" : ""} ${cls}" data-pid="${p.id}"${url ? ` style="--img:url('${url}')"` : ""}>${url ? "" : esc((p.name || "?")[0])}</div>`;
}
function withPhoto(p) {
  if (p.has_photo === false) return;
  loadPhoto(p.id).then(() => paintPhoto(p.id));
}

// =========================================================
// Экраны
// =========================================================
const view = () => $("#view");

const screens = {
  home() {
    const { user, stats, level, achievements } = state.me;
    const inc = state.vibes.incoming.length;
    const mut = state.vibes.mutual;
    const next = nextGoal(achievements);
    const greet = stats.streak_days > 1 ? `Серия ${days(stats.streak_days)}, не сбавляй 🔥` : "Отличный день, чтобы найти своих";

    const acts = [];
    if (inc) acts.push(["💌", `Тебя выбрали: ${inc}`, "Посмотри, кто это, и ответь", "vibes"]);
    mut.slice(0, 2).forEach((m) => acts.push(["💞", `Взаимный вайб с ${esc(m.name)}`, "Напиши первым, это работает", "vibes"]));

    return `
      <h1>Привет, ${esc(user.name)} 👋</h1>
      <p class="sub">${greet}</p>

      <div class="hero">
        <h2>Найди тех, кто на одной волне</h2>
        <p>Сначала вайб, потом фото. Оно откроется, когда лайк взаимный</p>
        <button class="btn btn-fill" data-go="search">${svg("heart")} Найти вайб</button>
        <div class="hero-mark" style="position:absolute;right:16px;top:20px;opacity:.95">${brandMark().replace('class="brand-mark"', 'class="brand-mark" style="width:96px;height:62px"')}</div>
      </div>

      ${dailyHtml()}

      <div class="tiles">
        <button class="tile" data-go="vibes"><div class="ti c-pink">${svg("heart")}</div>${inc ? `<span class="badge">${inc}</span>` : ""}<div><b>Мои вайбы</b><small>${inc ? `${inc} ${plural(inc, "новый", "новых", "новых")}` : `${mut.length} взаимных`}</small></div></button>
        <button class="tile" data-go="games"><div class="ti c-blue">${svg("game")}</div><div><b>Игры</b><small>1 на 1</small></div></button>
        <button class="tile" data-go="fame"><div class="ti c-gold">${svg("crown")}</div><div><b>Зал славы</b><small>${level.done} из ${level.total}</small></div></button>
      </div>

      <div class="grid g-auto mt">
        <div class="card strong"><p class="label">Твой уровень</p>${levelRow(level)}</div>
        <button class="card" data-go="fame" style="text-align:left">
          <p class="label">Ближайшая цель</p>${next ? goalRow(next) : `<p class="muted" style="margin:0">Всё открыто. Ты легенда 👑</p>`}
        </button>
      </div>

      ${acts.length ? `<div class="card mt"><p class="label">Что нового</p><div class="list">
        ${acts.map(([ic, t, s, to]) => `<button class="item" data-go="${to}"><div class="ii">${ic}</div><div class="grow"><b>${t}</b><small>${s}</small></div>${svg("chev", "chev")}</button>`).join("")}
      </div></div>` : ""}

      ${inviteHtml()}`;
  },

  search() {
    const sg = state.me.user.search_gender;
    return `
      <div class="search-head"><h1>Поиск вайба</h1><div class="row" style="gap:8px"><span id="undo-slot"></span><button class="icon-btn" style="width:40px;height:40px" data-go="settings" aria-label="Настройки">${svg("gear")}</button></div></div>
      <div class="seg" style="margin-bottom:14px">
        ${[["all", "Все"], ["female", "Девушки"], ["male", "Парни"]].map(([v, l]) =>
          `<button data-sg="${v}" class="${sg === v ? "on" : ""}">${l}</button>`).join("")}
      </div>
      <div class="deck" id="deck"><div class="skeleton"></div></div>
      <div class="actions" id="deck-actions" style="visibility:hidden">
        <button class="btn btn-ghost" id="btn-skip">${svg("x")} Дальше</button>
        <button class="icon-btn" id="btn-question" aria-label="Задать вопрос">${svg("chat")}</button>
        <button class="btn btn-pink" id="btn-like">${svg("heart")} Вайб</button>
      </div>`;
  },

  vibes() {
    const { incoming, mutual } = state.vibes;
    const tab = state.vibesTab;
    const inRow = (p) => `
      <div class="person" data-details="${p.id}">
        ${avatarFor(p)}
        <div class="grow"><b>${esc(p.name)}, ${p.age}</b><small>📍 ${esc(p.city || "")} · 🔥 ${p.vibe}%</small></div>
        <div class="acts">
          <button class="icon-btn" style="width:38px;height:38px" data-in-skip="${p.id}" aria-label="Дальше">${svg("x")}</button>
          <button class="btn btn-pink btn-sm" data-in-like="${p.id}">${svg("heart")} Вайб</button>
        </div>
      </div>`;
    const mRow = (p) => `
      <div class="person mutual">
        ${avatarFor(p, "pink")}
        <div class="grow"><b>${esc(p.name)}, ${p.age}</b><small>📍 ${esc(p.city || "")}</small></div>
        <button class="btn btn-pink btn-sm" data-write="${p.id}">${svg("chat")} Написать</button>
      </div>`;
    const list = tab === "in"
      ? (incoming.length ? incoming.map(inRow).join("") : emptyHtml("💌", "Пока тихо", "Лайкай смелее, и тебя заметят. Входящие вайбы появятся здесь"))
      : (mutual.length ? mutual.map(mRow).join("") : emptyHtml("💞", "Взаимных пока нет", "Здесь будут люди, с которыми вайб совпал. Им открыто твоё фото, а тебе их"));
    return `
      <h1>Мои вайбы</h1>
      <p class="sub">Кто тебя выбрал и с кем совпало</p>
      <div class="seg" style="margin-bottom:14px">
        <button data-vt="in" class="${tab === "in" ? "on" : ""}">Тебя выбрали<span class="count">${incoming.length}</span></button>
        <button data-vt="mutual" class="${tab === "mutual" ? "on" : ""}">Взаимные<span class="count">${mutual.length}</span></button>
      </div>
      <div class="list">${list}</div>`;
  },

  games() {
    return `
      <h1>Игры</h1>
      <p class="sub">Быстрый способ понять, на одной ли вы волне</p>
      <div id="game-root"></div>`;
  },

  profile() {
    const { user, stats, level, achievements } = state.me;
    const url = state.photos[user.id];
    return `
      <div class="card strong">
        <div class="profile-head">
          <button class="profile-photo ${url ? "photo" : ""}" id="photo-btn" data-pid="${user.id}" ${url ? `style="--img:url('${url}')"` : ""}>
            ${url ? "" : esc(user.name[0])}<span class="photo-edit">${svg("camera")}</span>
          </button>
          <div class="grow">
            <h1 style="margin:0">${esc(user.name)}, ${user.age}</h1>
            <div class="muted">📍 ${esc(user.city || "")}</div>
            <div class="mt" style="margin-top:8px"><span class="pill" style="border-color:rgba(255,200,97,.5);color:var(--gold)">👑 ${level.name}</span></div>
          </div>
        </div>
        ${user.about ? `<p style="margin:14px 0 0;color:#ddd5f5">${esc(user.about)}</p>` : ""}
        <div class="chips mt">${user.interests.map((t) => `<span class="chip">${esc(t)}</span>`).join("")}</div>
        <div class="grid g2 mt">
          <button class="btn btn-violet btn-sm" data-go="edit" style="height:42px">${svg("edit")} Редактировать</button>
          <button class="btn btn-ghost btn-sm" id="invite-btn" style="height:42px">${svg("share")} Пригласить</button>
        </div>
      </div>

      <div class="grid g4 mt">
        ${statTile(svg("heart"), stats.likes_sent, "лайков")}
        ${statTile(svg("heart"), stats.mutual_likes, "взаимных")}
        ${statTile(svg("game"), stats.games, "игр")}
        ${statTile(svg("fire"), stats.streak_days, "серия")}
      </div>

      <div class="card mt">
        <div class="row between" style="margin-bottom:14px"><p class="label" style="margin:0">Достижения · ${level.done} из ${level.total}</p><button class="btn btn-ghost btn-sm" data-go="fame">Все</button></div>
        <div class="ach-grid">${sortAch(achievements).slice(0, 4).map(achHtml).join("")}</div>
      </div>
      <div class="list mt">
        <button class="item" data-go="stats"><div class="ii">📊</div><div class="grow"><b>Статистика</b><small>Твои цифры</small></div>${svg("chev", "chev")}</button>
        <button class="item" data-go="settings"><div class="ii">⚙️</div><div class="grow"><b>Настройки</b><small>Поиск, приватность, помощь</small></div>${svg("chev", "chev")}</button>
      </div>`;
  },

  edit() {
    const f = state.form || (state.form = {
      name: state.me.user.name, city: state.me.user.city || "", about: state.me.user.about || "",
      interests: state.me.user.interests.slice(), search_gender: state.me.user.search_gender,
    });
    const url = state.photos[state.me.user.id];
    const have = new Set(f.interests.map((x) => x.toLowerCase()));
    const sugg = SUGGESTED.filter((s) => !have.has(s)).slice(0, 12);
    return `
      <h1>Анкета</h1>
      <p class="sub">Возраст и пол меняются только в боте</p>

      <div class="row">
        <button class="profile-photo ${url ? "photo" : ""}" id="photo-btn" data-pid="${state.me.user.id}" style="width:84px;height:84px;font-size:30px;${url ? `--img:url('${url}')` : ""}">
          ${url ? "" : esc(f.name[0] || "?")}<span class="photo-edit">${svg("camera")}</span>
        </button>
        <div class="grow small muted">Фото увидят только те, с кем вайб взаимный. Лучше всего — лицо при хорошем свете</div>
      </div>

      <label class="field-label" for="f-name">Имя</label>
      <input class="field" id="f-name" maxlength="30" value="${esc(f.name)}" autocomplete="off">
      <label class="field-label" for="f-city">Город</label>
      <input class="field" id="f-city" maxlength="50" value="${esc(f.city)}" autocomplete="off">
      <label class="field-label" for="f-about">О себе</label>
      <textarea class="field" id="f-about" rows="4" maxlength="500">${esc(f.about)}</textarea>
      <div class="field-hint"><span>Пара фраз, которые цепляют</span><span id="about-count">${f.about.length} / 500</span></div>

      <label class="field-label">Интересы · до 10</label>
      <div class="chips" id="my-tags">${f.interests.map((t, i) => `<button class="chip common" data-rm="${i}">${esc(t)}<span class="x">✕</span></button>`).join("")}</div>
      <div class="tag-input">
        <input class="field" id="f-tag" maxlength="30" placeholder="Например: сноуборд" autocomplete="off" enterkeyhint="done">
        <button class="icon-btn" id="add-tag" aria-label="Добавить">${svg("plus")}</button>
      </div>
      ${sugg.length ? `<div class="chips suggest">${sugg.map((s) => `<button class="chip" data-add="${esc(s)}">+ ${esc(s)}</button>`).join("")}</div>` : ""}

      <label class="field-label">Кого показывать</label>
      <div class="seg" id="f-sg">${[["all", "Всех"], ["female", "Девушек"], ["male", "Парней"]].map(([v, l]) =>
        `<button data-fsg="${v}" class="${f.search_gender === v ? "on" : ""}">${l}</button>`).join("")}</div>

      <div class="save-bar"><button class="btn btn-fill btn-block" id="save-profile">Сохранить</button></div>`;
  },

  fame() {
    const list = state.me.achievements;
    const f = state.fameFilter;
    const shown = sortAch(list).filter((a) => f === "all" || (f === "open" ? a.done : !a.done));
    const { level } = state.me;
    return `
      <h1>Зал славы</h1>
      <p class="sub">Открыто ${level.done} из ${level.total}${level.next_at > level.done ? ` · до уровня ${level.n + 1} ещё ${level.next_at - level.done}` : ""}</p>
      <div class="card strong" style="margin-bottom:12px">${levelRow(level)}</div>
      <div class="seg" style="margin-bottom:14px">
        ${[["all", "Все"], ["open", "Открытые"], ["locked", "Впереди"]].map(([v, l]) =>
          `<button data-fame="${v}" class="${f === v ? "on" : ""}">${l}</button>`).join("")}
      </div>
      <div class="card">${shown.length ? `<div class="ach-grid">${shown.map(achHtml).join("")}</div>` : emptyHtml("🏆", "Пока пусто", "Лайкай, играй и заходи каждый день — достижения откроются")}</div>`;
  },

  stats() {
    const { stats, level } = state.me;
    const pct = Math.round((level.done / level.total) * 100);
    return `
      <h1>Статистика</h1>
      <p class="sub">Твой вайб в цифрах</p>
      <div class="card strong" style="display:flex;flex-direction:column;align-items:center;padding:22px 16px">
        ${gauge(pct, 190, "прогресс")}
        <p class="muted small" style="margin:10px 0 0">Уровень ${level.n} · ${level.name} · ${level.done} из ${level.total} достижений</p>
      </div>
      <div class="grid g2 mt">
        ${statTile(svg("heart"), stats.likes_sent, "лайков поставил")}
        ${statTile(svg("mail"), stats.likes_received, "тебя выбрали")}
        ${statTile(svg("heart"), stats.mutual_likes, "взаимных вайбов")}
        ${statTile(svg("game"), stats.games, "игр сыграно")}
        ${statTile(svg("chat"), `${stats.questions_sent} / ${stats.questions_received}`, "вопросов задал / получил")}
        ${statTile(svg("fire"), days(stats.best_streak), "рекорд серии")}
      </div>`;
  },

  settings() {
    const sg = state.me.user.search_gender;
    const item = (ic, t, s, id) => `<button class="item" id="${id}"><div class="ii">${ic}</div><div class="grow"><b>${t}</b><small>${s}</small></div>${svg("chev", "chev")}</button>`;
    return `
      <h1>Настройки</h1>
      <p class="sub">Всё под твоим контролем</p>
      <div class="card"><p class="label">Кого показывать в поиске</p>
        <div class="seg">${[["all", "Всех"], ["female", "Девушек"], ["male", "Парней"]].map(([v, l]) =>
          `<button data-sg="${v}" class="${sg === v ? "on" : ""}">${l}</button>`).join("")}</div>
      </div>
      <div class="list mt">
        ${item(svg("edit"), "Анкета и фото", "Имя, город, о себе, интересы", "set-edit")}
        ${item(svg("spark"), "Как работает Вайбометр", "Коротко за 15 секунд", "set-onb")}
        ${item(svg("share"), "Позвать друга", "Чем больше своих, тем больше вайба", "set-invite")}
        ${item(svg("lock"), "Приватность", "Кто видит твоё фото и данные", "set-privacy")}
        ${item(svg("ban"), "Заблокированные и удаление", "В чате с ботом → ⚙️ Настройки", "set-bot")}
      </div>
      <p class="small muted" style="text-align:center;margin-top:22px">Вайбометр · только 18+ · <span class="grad-text" style="font-weight:800">Твой круг. Твой вайб.</span></p>`;
  },
};

function statTile(ic, v, l) {
  return `<div class="stat"><span class="si">${ic}</span><b>${v}</b><small>${l}</small></div>`;
}

function emptyHtml(icon, title, text) {
  return `<div class="empty"><div class="big">${icon}</div><h2>${title}</h2><p>${text}</p></div>`;
}

function levelRow(level) {
  const span = Math.max(1, level.next_at - (level.next_at > level.done ? prevAt(level) : 0));
  const pct = level.next_at > level.done ? Math.round(((level.done - prevAt(level)) / span) * 100) : 100;
  return `
    <div class="level">
      <div class="level-badge">${level.n}</div>
      <div class="grow">
        <div class="row between"><b>${level.name}</b><span class="small muted">${level.next_at > level.done ? `ещё ${level.next_at - level.done} до ур. ${level.n + 1}` : "максимум"}</span></div>
        <div class="bar" style="margin-top:9px"><i style="width:${Math.max(4, pct)}%"></i></div>
      </div>
    </div>`;
}
// с какого числа достижений начался текущий уровень (ступени как в ui.LEVELS)
function prevAt(level) {
  return [0, 2, 4, 6, level.total][level.n - 1] ?? 0;
}

function nextGoal(list) {
  return list.filter((a) => !a.done).sort((a, b) => b.value / b.goal - a.value / a.goal)[0];
}
function sortAch(list) {
  return list.slice().sort((a, b) => (b.done - a.done) || (b.value / b.goal - a.value / a.goal));
}

function goalRow(a) {
  const pct = Math.min(100, Math.round((a.value / a.goal) * 100));
  return `
    <div class="row">
      <div class="goal-icon">${a.icon}</div>
      <div class="grow">
        <div class="row between"><b>${esc(a.name)}</b><span class="small muted">${a.value} / ${a.goal}</span></div>
        <div class="small muted">${esc(a.hint)}</div>
        <div class="bar" style="margin-top:8px"><i style="width:${Math.max(4, pct)}%"></i></div>
      </div>
    </div>`;
}

function achHtml(a) {
  const pct = Math.min(100, Math.round((a.value / a.goal) * 100));
  return `
    <div class="ach ${a.done ? "done" : "locked"}">
      <div class="medal"><span>${a.icon}</span></div>
      <b>${esc(a.name)}</b>
      <small>${a.done ? "открыто" : `${a.value} из ${a.goal}`}</small>
      ${a.done ? "" : `<div class="bar"><i style="width:${Math.max(4, pct)}%"></i></div>`}
    </div>`;
}

function inviteHtml() {
  return `<button class="invite" id="invite-btn"><span class="ii">📤</span><span class="grow"><b>Позови друзей</b><small>Чем больше своих в Вайбометре, тем больше вайба вокруг</small></span>${svg("chev", "chev")}</button>`;
}

const SUGGESTED = ["музыка", "кино", "спорт", "путешествия", "игры", "аниме", "книги", "фотография", "танцы", "кофе",
  "мемы", "фитнес", "искусство", "технологии", "готовка", "сериалы", "концерты", "йога", "животные", "бизнес"];

// =========================================================
// Поиск: колода, свайп, «Вернуть»
// =========================================================
async function loadCandidate(prefetched) {
  const deck = $("#deck");
  if (!deck) return;
  let c = prefetched;
  if (c === undefined) {
    try {
      c = (await api.next()).candidate;
    } catch (e) {
      deck.innerHTML = errorHtml(e);
      return;
    }
  }
  if (!$("#deck")) return;
  state.candidate = c;
  $("#deck-actions").style.visibility = c ? "visible" : "hidden";

  $("#undo-slot").innerHTML = state.lastSkip ? `<button class="undo" id="btn-undo">${svg("undo")} Вернуть</button>` : "";
  if (!c) {
    deck.innerHTML = `${emptyHtml("🌙", "Анкеты закончились", "Новые люди приходят каждый день. Позови друзей — станет веселее")}
      <div style="text-align:center"><button class="btn btn-violet btn-sm" id="empty-invite">${svg("share")} Позвать друга</button></div>`;
    $("#empty-invite").onclick = invite;
  } else {
    deck.innerHTML = `<div class="pcard under"></div>${cardHtml(c)}`;
    bindSwipe($(".pcard:not(.under)", deck));
    animateGauges(deck);
    if (!store.get("vm_hint")) showSwipeHint();
  }
  const ub = $("#btn-undo");
  if (ub) ub.onclick = undoSkip;
}

function hue(id) {
  const palettes = [["#b04cff", "#ff3d9a"], ["#6d5bff", "#c13cff"], ["#ff3d9a", "#ff8a3d"], ["#3d7bff", "#b04cff"], ["#c13cff", "#3dd6ff"]];
  return palettes[Math.abs(id) % palettes.length];
}

function tagsHtml(p) {
  const common = new Set((p.common || []).map((x) => x.toLowerCase()));
  const list = (p.interests || []).slice().sort((a, b) => common.has(b.toLowerCase()) - common.has(a.toLowerCase()));
  return list.map((t) => `<span class="chip ${common.has(t.toLowerCase()) ? "common" : ""}">${common.has(t.toLowerCase()) ? "✦ " : ""}${esc(t)}</span>`).join("");
}

function dailyHtml() {
  const d = state.me.daily;
  if (!d) return "";
  const body = d.answer
    ? `<p class="muted" style="margin:0">Твой ответ: <b>${esc(d[d.answer])}</b>. Его увидят в поиске. Завтра будет новый вопрос</p>`
    : `<div class="daily-btns"><button class="btn btn-ghost" data-daily="a">${esc(d.a)}</button><button class="btn btn-ghost" data-daily="b">${esc(d.b)}</button></div>`;
  return `<div class="card daily"><p class="label">Вайб дня</p><b class="daily-q">${esc(d.text)}</b>${body}</div>`;
}

function cardHtml(c) {
  const [a1, a2] = hue(c.id);
  return `
    <div class="pcard enter" style="--a1:${a1};--a2:${a2}">
      <div class="stamp like">ВАЙБ</div>
      <div class="stamp skip">ДАЛЬШЕ</div>
      <div class="aura">
        ${c.same_city ? `<span class="pill ok card-tag">📍 Твой город</span>` : ""}
        <button class="card-menu" data-act="menu" aria-label="Ещё">${svg("more")}</button>
        <div class="silhouette">${esc((c.name || "?")[0])}</div>
        <div class="lock-note">${svg("lock")} Фото откроется после взаимного вайба</div>
      </div>
      <div class="pinfo" data-act="details">
        <div class="top">
          <div class="grow"><div class="pname">${esc(c.name)}, ${c.age}</div><div class="pcity">📍 ${esc(c.city || "")}</div></div>
          ${gauge(c.vibe, 78)}
        </div>
        ${c.daily ? `<div class="chips" style="margin-bottom:8px"><span class="chip daily-chip ${c.daily.match ? "common" : ""}">${c.daily.match ? "✦ " : ""}Вайб дня: ${esc(c.daily.label)}</span></div>` : ""}
        <div class="chips">${tagsHtml(c)}</div>
        ${c.about ? `<p class="pabout">${esc(c.about)}</p>` : ""}
        <div class="more-hint">Нажми, чтобы открыть анкету целиком</div>
      </div>
    </div>`;
}

function showSwipeHint() {
  const deck = $("#deck");
  deck.insertAdjacentHTML("beforeend", `
    <div class="swipe-hint" id="swipe-hint"><div>
      <div class="hand">👆</div>
      <p>Вправо — <span class="grad-text">вайб</span>, влево — мимо<br><span class="muted small">Или жми кнопки внизу</span></p>
      <button class="btn btn-violet btn-sm">Понятно</button>
    </div></div>`);
  $("#swipe-hint button").onclick = () => { store.set("vm_hint", "1"); $("#swipe-hint").remove(); };
}

function bindSwipe(card) {
  let x0 = 0, y0 = 0, dx = 0, dragging = false, moved = false, downTarget = null;
  const like = $(".stamp.like", card), skip = $(".stamp.skip", card);

  card.addEventListener("pointerdown", (e) => {
    dragging = true; moved = false; x0 = e.clientX; y0 = e.clientY; dx = 0;
    downTarget = e.target;
    card.setPointerCapture(e.pointerId);
    card.style.transition = "none";
  });
  card.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    dx = e.clientX - x0;
    if (Math.abs(dx) > 6) moved = true;
    if (!moved) return;
    card.style.transform = `translate(${dx}px, ${(e.clientY - y0) * 0.15}px) rotate(${dx / 18}deg)`;
    like.style.opacity = Math.max(0, Math.min(1, dx / 90));
    skip.style.opacity = Math.max(0, Math.min(1, -dx / 90));
  });
  const end = () => {
    if (!dragging) return;
    dragging = false;
    if (!moved) {
      // тап: меню «⋯» или полная анкета
      const act = downTarget && downTarget.closest("[data-act]");
      if (act && act.dataset.act === "menu") openCardMenu(state.candidate);
      else if (act && act.dataset.act === "details") openDetails(state.candidate, "search");
      return;
    }
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

let busy = false;
async function decide(action) {
  const c = state.candidate;
  const card = $("#deck .pcard:not(.under)");
  if (!c || !card || busy) return;
  busy = true;
  haptic(action === "like" ? "medium" : "light");
  $("#swipe-hint") && ($("#swipe-hint").remove(), store.set("vm_hint", "1"));
  $("#btn-undo") && $("#btn-undo").remove();

  const dir = action === "like" ? 1 : -1;
  card.style.transition = "transform .35s ease, opacity .35s ease";
  card.style.transform = `translate(${dir * 560}px, -30px) rotate(${dir * 22}deg)`;
  card.style.opacity = "0";
  $(action === "like" ? ".stamp.like" : ".stamp.skip", card).style.opacity = 1;

  try {
    const res = await api.vibe(c.id, action);
    state.lastSkip = action === "skip" ? c : null;
    if (res.mutual) { showMatch(res.match); refreshSoft(); }
  } catch (e) {
    toast(errorText(e));
  }
  setTimeout(() => { busy = false; loadCandidate(); }, 280);
}

async function undoSkip() {
  const p = state.lastSkip;
  if (!p || busy) return;
  busy = true;
  haptic("light");
  try {
    const { candidate } = await api.undo(p.id);
    state.lastSkip = null;
    busy = false;
    loadCandidate(candidate);
  } catch (_) {
    busy = false;
    state.lastSkip = null;
    $("#btn-undo") && $("#btn-undo").remove();
    toast("Вернуть не получилось");
  }
}

// =========================================================
// Шторки: полная анкета, меню, вопрос, жалоба, приватность
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
  const sheet = $("#sheet");
  sheet.innerHTML = `<div class="sheet-backdrop" data-close></div><div class="sheet-panel"><div class="sheet-grip"></div>${html}</div>`;
  sheet.classList.remove("hidden");
  $$("[data-close]", sheet).forEach((el) => el.onclick = closeSheet);
  return sheet;
}
function closeSheet() { $("#sheet").classList.add("hidden"); }
const sheetOpen = () => !$("#sheet").classList.contains("hidden");

function openDetails(p, from) {
  if (!p) return;
  const [a1, a2] = hue(p.id);
  const sheet = openSheet(`
    <div class="row" style="align-items:flex-start">
      <div class="aura" style="--a1:${a1};--a2:${a2};margin:0;flex:none;width:96px;height:96px;min-height:0"><div class="silhouette" style="width:64px;font-size:26px">${esc(p.name[0])}</div></div>
      <div class="grow"><div class="pname">${esc(p.name)}, ${p.age}</div><div class="pcity">📍 ${esc(p.city || "")}${p.same_city ? " · твой город" : ""}</div></div>
      ${gauge(p.vibe, 84, vibeWord(p.vibe))}
    </div>
    ${p.common && p.common.length ? `<p class="label mt-l">Общее · ${p.common.length}</p><div class="chips">${p.common.map((t) => `<span class="chip common">✦ ${esc(t)}</span>`).join("")}</div>` : ""}
    <p class="label mt-l">Интересы</p><div class="chips">${tagsHtml(p)}</div>
    ${p.about ? `<p class="label mt-l">О себе</p><p style="margin:0;color:#ddd5f5;white-space:pre-line">${esc(p.about)}</p>` : ""}
    <div class="lock-note" style="position:static;margin-top:18px">${svg("lock")} Фото откроется после взаимного вайба</div>
    <div class="actions" style="margin-top:16px">
      <button class="btn btn-ghost" data-d="skip">${svg("x")} Дальше</button>
      <button class="icon-btn" data-d="question" aria-label="Вопрос">${svg("chat")}</button>
      <button class="btn btn-pink" data-d="like">${svg("heart")} Вайб</button>
    </div>
    <button class="btn btn-ghost btn-block btn-sm mt" data-d="report">${svg("flag")} Пожаловаться</button>`);
  animateGauges(sheet);
  $$("[data-d]", sheet).forEach((b) => b.onclick = () => {
    const d = b.dataset.d;
    if (d === "question") return openQuestion(p);
    if (d === "report") return openReport(p, from);
    closeSheet();
    if (from === "search") decide(d);
    else incomingAction(p.id, d);
  });
}

function openCardMenu(p) {
  if (!p) return;
  const sheet = openSheet(`
    <h2 class="sheet-title">${esc(p.name)}, ${p.age}</h2>
    <div class="list mt">
      <button class="item" data-m="details"><div class="ii">👀</div><div class="grow"><b>Открыть анкету</b><small>Интересы и о себе целиком</small></div></button>
      <button class="item" data-m="question"><div class="ii">💬</div><div class="grow"><b>Задать вопрос</b><small>Анонимно, ответ придёт в бота</small></div></button>
      <button class="item" data-m="report"><div class="ii">⚠️</div><div class="grow"><b>Пожаловаться</b><small>Анкета пропадёт из выдачи</small></div></button>
    </div>
    <button class="btn btn-ghost btn-block mt" data-close>Отмена</button>`);
  $$("[data-close]", sheet).forEach((el) => el.onclick = closeSheet);
  $$("[data-m]", sheet).forEach((b) => b.onclick = () => {
    if (b.dataset.m === "details") openDetails(p, "search");
    if (b.dataset.m === "question") openQuestion(p);
    if (b.dataset.m === "report") openReport(p, "search");
  });
}

function openQuestion(p) {
  const sheet = openSheet(`
    <h2 class="sheet-title">Вопрос · ${esc(p.name)}</h2>
    <p class="muted small" style="margin:0 0 12px">Анонимно: ${esc(p.name)} не узнает, кто спросил</p>
    <textarea id="q-text" class="field" rows="4" maxlength="${QUESTION_MAX}" placeholder="Например: какой трек у тебя сейчас на репите?"></textarea>
    <div class="field-hint" style="margin-bottom:14px"><span>Ответ придёт в чат с ботом</span><span id="q-count">0 / ${QUESTION_MAX}</span></div>
    <div class="chips" style="margin-bottom:14px">
      ${["Какой трек сейчас на репите?", "Идеальный выходной — это…", "Кофе или чай?"].map((q) => `<button class="chip" data-q="${esc(q)}">${esc(q)}</button>`).join("")}
    </div>
    <button class="btn btn-violet btn-block" id="q-send" disabled>${svg("chat")} Отправить</button>`);
  const area = $("#q-text", sheet), send = $("#q-send", sheet);
  const sync = () => {
    $("#q-count", sheet).textContent = `${area.value.length} / ${QUESTION_MAX}`;
    send.disabled = area.value.trim().length === 0;
  };
  area.oninput = sync;
  $$("[data-q]", sheet).forEach((c) => c.onclick = () => { area.value = c.dataset.q; sync(); area.focus(); });
  send.onclick = async () => {
    send.disabled = true;
    try {
      await api.question(p.id, area.value.trim());
      haptic("success");
      closeSheet();
      toast("Вопрос улетел 💬");
    } catch (e) {
      send.disabled = false;
      toast(e.code === "not_delivered" ? "Не доставлено: человек закрыл бота" : errorText(e));
    }
  };
}

function openReport(p, from) {
  const sheet = openSheet(`
    <h2 class="sheet-title">Пожаловаться · ${esc(p.name)}</h2>
    <p class="muted small" style="margin:0 0 12px">Анкета сразу пропадёт из твоей выдачи, модератор проверит</p>
    <div class="list">${REPORT_REASONS.map(([code, label]) =>
      `<button class="item" data-reason="${code}"><div class="grow"><b>${label}</b></div>${svg("chev", "chev")}</button>`).join("")}</div>
    <button class="btn btn-ghost btn-block mt" data-close>Отмена</button>`);
  $$("[data-close]", sheet).forEach((el) => el.onclick = closeSheet);
  $$("[data-reason]", sheet).forEach((b) => b.onclick = async () => {
    try {
      await api.report(p.id, b.dataset.reason);
      haptic("success");
      closeSheet();
      toast("Жалоба отправлена, спасибо 🙏");
      if (from === "search") dismissCard();
      else { await refreshSoft(); render(); }
    } catch (e) {
      toast(errorText(e));
    }
  });
}

function dismissCard() {
  const card = $("#deck .pcard:not(.under)");
  if (card) {
    card.style.transition = "transform .3s ease, opacity .3s ease";
    card.style.transform = "translateY(40px) scale(.9)";
    card.style.opacity = "0";
  }
  state.lastSkip = null;
  setTimeout(() => loadCandidate(), 300);
}

function openPrivacy() {
  openSheet(`
    <h2 class="sheet-title">🔒 Приватность</h2>
    <div class="list mt">
      <div class="item"><div class="ii">📸</div><div class="grow"><b>Фото</b><small>Видят только люди со взаимным вайбом</small></div></div>
      <div class="item"><div class="ii">💬</div><div class="grow"><b>Вопросы</b><small>Анонимные: никто не узнает, кто спросил</small></div></div>
      <div class="item"><div class="ii">👤</div><div class="grow"><b>Контакт</b><small>Ссылка на тебя открывается только при взаимности</small></div></div>
      <div class="item"><div class="ii">🗑</div><div class="grow"><b>Удаление</b><small>В боте: ⚙️ Настройки → Удалить профиль. Стирается всё</small></div></div>
    </div>
    <button class="btn btn-ghost btn-block mt" data-close>Понятно</button>`);
}

// =========================================================
// Взаимность
// =========================================================
function showMatch(m) {
  const me = state.me.user;
  const ov = $("#overlay");
  const colors = ["#ff3d9a", "#c084fc", "#ff7ac3", "#9b5cff", "#ffc861"];
  const confetti = Array.from({ length: 34 }, (_, i) =>
    `<span class="confetti" style="left:${Math.random() * 100}%;color:${colors[i % 5]};font-size:${10 + Math.random() * 16}px;animation-duration:${2.4 + Math.random() * 2.6}s;animation-delay:${Math.random() * 1.2}s">${i % 3 ? "\u2665\uFE0E" : "\u2726"}</span>`).join("");
  ov.innerHTML = `
    ${confetti}
    <h1 class="match-title">Взаимный вайб!</h1>
    <p class="muted" style="margin:6px 0 0">Вы понравились друг другу. Фото открыто</p>
    <div class="match-pair">
      <div class="who">${avatarFor(me, "xl")}<b>${esc(me.name)}</b><small>${me.age}</small></div>
      <div class="match-heart">💗</div>
      <div class="who">${avatarFor(m, "xl pink")}<b>${esc(m.name)}</b><small>${m.age}</small></div>
    </div>
    ${m.vibe ? `<div style="margin-top:6px">${gauge(m.vibe, 120, vibeWord(m.vibe))}</div>` : ""}
    ${(m.openers || []).length ? `<div class="openers"><p class="label">С чего начать</p>${m.openers.map((t, i) => `<button class="opener" data-op="${i}">${esc(t)}</button>`).join("")}</div>` : ""}
    <div class="match-actions">
      <button class="btn btn-fill" id="match-write">${svg("chat")} Написать первым</button>
      <button class="btn btn-ghost" id="match-close">Искать дальше</button>
    </div>`;
  ov.classList.remove("hidden");
  animateGauges(ov);
  $("#match-write").onclick = () => writeTo(m);
  $$("[data-op]").forEach((b) => b.onclick = () => {
    haptic("select");
    const text = m.openers[Number(b.dataset.op)];
    try { navigator.clipboard.writeText(text); toast("Скопировано, вставь в чат"); } catch (_) { toast("Не удалось скопировать"); }
    writeTo(m);
  });
  $("#match-close").onclick = () => ov.classList.add("hidden");
  withPhoto(me);
  withPhoto(m);
}

function writeTo(p) {
  haptic("light");
  if (DEMO) { toast(`Откроется чат с ${p.name}`); return; }
  if (p.username) tg.openTelegramLink(`https://t.me/${p.username}`);
  else toast("Ссылка на профиль пришла тебе в чат с ботом");
}

// =========================================================
// Входящие
// =========================================================
async function incomingAction(id, action) {
  const p = state.vibes.incoming.find((x) => x.id === id);
  haptic(action === "like" ? "medium" : "light");
  try {
    const res = await api.vibe(id, action);
    if (res.mutual) showMatch(res.match || p);
    else if (action === "like") toast("Вайб отправлен 💜");
    await refreshSoft();
    if (route() === "vibes") render();
  } catch (e) {
    toast(errorText(e));
  }
}

// =========================================================
// Анкета: сохранение и фото
// =========================================================
function bindEdit() {
  const f = state.form;
  const name = $("#f-name"), city = $("#f-city"), about = $("#f-about"), tag = $("#f-tag");
  name.oninput = () => { f.name = name.value; name.classList.remove("bad"); };
  city.oninput = () => { f.city = city.value; city.classList.remove("bad"); };
  about.oninput = () => { f.about = about.value; $("#about-count").textContent = `${about.value.length} / 500`; about.classList.remove("bad"); };

  const addTag = (raw) => {
    const t = String(raw || "").replace(/,/g, " ").replace(/\s+/g, " ").trim().toLowerCase().slice(0, 30);
    if (!t) return;
    if (f.interests.length >= 10) { toast("Максимум 10 интересов"); return; }
    if (!f.interests.some((x) => x.toLowerCase() === t)) f.interests.push(t);
    haptic("select");
    rerenderEdit();
  };
  $("#add-tag").onclick = () => addTag(tag.value);
  tag.onkeydown = (e) => { if (e.key === "Enter" || e.key === ",") { e.preventDefault(); addTag(tag.value); } };
  $$("[data-add]").forEach((b) => b.onclick = () => addTag(b.dataset.add));
  $$("[data-rm]").forEach((b) => b.onclick = () => { f.interests.splice(Number(b.dataset.rm), 1); haptic("select"); rerenderEdit(); });
  $$("[data-fsg]").forEach((b) => b.onclick = () => { f.search_gender = b.dataset.fsg; haptic("select"); rerenderEdit(); });
  $("#save-profile").onclick = saveProfile;
}

function rerenderEdit() {
  const y = window.scrollY;
  view().innerHTML = screens.edit();
  bindEdit();
  bindPhotoButton();
  window.scrollTo(0, y);
}

async function saveProfile() {
  const f = state.form;
  const data = {
    name: f.name.trim(), city: f.city.trim(), about: f.about.trim(),
    interests: f.interests, search_gender: f.search_gender,
  };
  const bad = (id, msg) => { const el = $(id); el && el.classList.add("bad"); el && el.focus(); toast(msg); haptic("error"); };
  if (data.name.length < 2 || data.name.length > 30) return bad("#f-name", "Имя: от 2 до 30 символов");
  if (data.city.length < 2 || data.city.length > 50) return bad("#f-city", "Город: от 2 до 50 символов");
  if (!data.about || data.about.length > 500) return bad("#f-about", "Напиши пару слов о себе, до 500 символов");
  if (!data.interests.length) return bad("#f-tag", "Добавь хотя бы один интерес");

  const btn = $("#save-profile");
  btn.disabled = true; btn.textContent = "Сохраняем…";
  try {
    await api.saveProfile(data);
    haptic("success");
    state.form = null;
    await refreshSoft();
    toast("Анкета обновлена ✨");
    go("profile");
  } catch (e) {
    btn.disabled = false; btn.textContent = "Сохранить";
    const map = { bad_name: "Имя: от 2 до 30 символов", bad_city: "Не похоже на город", bad_about: "О себе: до 500 символов", bad_interests: "Проверь интересы" };
    toast(map[e.code] || errorText(e));
  }
}

function bindPhotoButton() {
  const btn = $("#photo-btn");
  if (btn) btn.onclick = () => $("#photo-input").click();
}

$("#photo-input").addEventListener("change", async (e) => {
  const file = e.target.files && e.target.files[0];
  e.target.value = "";
  if (!file) return;
  const btn = $("#photo-btn");
  btn && btn.classList.add("uploading");
  try {
    const blob = await compressImage(file);
    await api.uploadPhoto(blob);
    const id = state.me.user.id;
    if (state.photos[id]) URL.revokeObjectURL(state.photos[id]);
    delete state.photos[id];
    if (DEMO) state.photos[id] = URL.createObjectURL(blob);
    else await loadPhoto(id);
    state.me.user.has_photo = true;
    haptic("success");
    toast("Фото обновлено 📸");
    renderChrome();
    if (route() === "edit") rerenderEdit(); else render();
  } catch (err) {
    const map = { too_big: "Файл слишком большой", bad_type: "Нужна картинка JPG или PNG", upload_failed: "Не получилось загрузить, попробуй ещё раз" };
    toast(map[err.code] || "Не получилось загрузить фото");
  } finally {
    btn && btn.classList.remove("uploading");
  }
});

// Ужимаем до 1280px и JPEG, чтобы фото быстро летело даже по мобильному
function compressImage(file) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const k = Math.min(1, 1280 / Math.max(img.width, img.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(img.width * k);
      canvas.height = Math.round(img.height * k);
      canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      canvas.toBlob((b) => (b ? resolve(b) : reject(Object.assign(new Error(), { code: "bad_type" }))), "image/jpeg", 0.88);
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(Object.assign(new Error(), { code: "bad_type" })); };
    img.src = url;
  });
}


// =========================================================
// Карточка для сторис: «Мы совпали на N%»
// =========================================================
function loadImage(src) {
  return new Promise((resolve) => {
    const im = new Image();
    im.onload = () => resolve(im);
    im.onerror = () => resolve(null);
    im.src = src;
  });
}

// Текст с разрядкой (letterSpacing в canvas есть не везде, считаем сами)
function spaced(g, text, x, y, gap) {
  const chars = [...text];
  const widths = chars.map((ch) => g.measureText(ch).width);
  const total = widths.reduce((a, b) => a + b, 0) + gap * (chars.length - 1);
  const align = g.textAlign;
  g.textAlign = "left";
  let cx = align === "center" ? x - total / 2 : align === "right" ? x - total : x;
  chars.forEach((ch, i) => { g.fillText(ch, cx, y); cx += widths[i] + gap; });
  g.textAlign = align;
}

function heartPath(g, x, y, s) {
  g.beginPath();
  g.moveTo(x, y + s * 0.9);
  g.bezierCurveTo(x - s * 1.5, y - s * 0.1, x - s * 0.7, y - s * 0.9, x, y - s * 0.3);
  g.bezierCurveTo(x + s * 0.7, y - s * 0.9, x + s * 1.5, y - s * 0.1, x, y + s * 0.9);
  g.closePath();
}

// Фон без фото: неоновое боке ночного города
function drawNeonBackdrop(g, W, H) {
  let seed = 7;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  let r = g.createRadialGradient(W / 2, 520, 40, W / 2, 520, 1000);
  r.addColorStop(0, "rgba(120,60,220,.45)"); r.addColorStop(1, "rgba(120,60,220,0)");
  g.fillStyle = r; g.fillRect(0, 0, W, H);
  const colors = ["255,61,154", "155,92,255", "90,140,255", "255,122,195"];
  for (let i = 0; i < 46; i++) {
    const x = rnd() * W, y = rnd() * H * 0.85, rad = 20 + rnd() * 70;
    const col = colors[Math.floor(rnd() * colors.length)];
    const bg = g.createRadialGradient(x, y, 0, x, y, rad);
    bg.addColorStop(0, `rgba(${col},${0.25 + rnd() * 0.3})`); bg.addColorStop(1, `rgba(${col},0)`);
    g.fillStyle = bg; g.beginPath(); g.arc(x, y, rad, 0, 2 * Math.PI); g.fill();
  }
}

// Картинка для сторис: «Я и Анастасия · 80%». Фон: webapp/share-bg.jpg, если лежит, иначе неоновый градиент
async function drawShareCard({ pct, name, matches, total, verdict }) {
  try { await Promise.all([document.fonts.load('700 100px "Unbounded"'), document.fonts.load('500 40px "Manrope"')]); } catch (_) {}
  const bg = await loadImage("share-bg.jpg");
  const W = 1080, H = 1920;
  const c = document.createElement("canvas");
  c.width = W; c.height = H;
  const g = c.getContext("2d");
  const head = '"Unbounded", "Manrope", system-ui, sans-serif';
  const body = '"Manrope", system-ui, sans-serif';
  const cx = W / 2;

  // фон
  g.fillStyle = "#07060d"; g.fillRect(0, 0, W, H);
  if (bg) {
    const k = Math.max(W / bg.width, H / bg.height);
    g.drawImage(bg, (W - bg.width * k) / 2, (H - bg.height * k) / 2, bg.width * k, bg.height * k);
  } else {
    drawNeonBackdrop(g, W, H);
  }
  // затемнение сверху и снизу, чтобы текст читался
  let v = g.createLinearGradient(0, 0, 0, H);
  v.addColorStop(0, "rgba(7,6,13,.55)"); v.addColorStop(0.25, "rgba(7,6,13,.05)");
  v.addColorStop(0.45, "rgba(7,6,13,.55)"); v.addColorStop(1, "rgba(7,6,13,.92)");
  g.fillStyle = v; g.fillRect(0, 0, W, H);

  g.textAlign = "center";
  // бренд
  g.strokeStyle = "#c084fc"; g.lineWidth = 7; g.lineCap = "round";
  g.beginPath(); g.arc(cx, 110, 34, Math.PI, 2 * Math.PI); g.stroke();
  g.strokeStyle = "#fff"; g.beginPath(); g.moveTo(cx, 110); g.lineTo(cx + 22, 86); g.stroke();
  g.fillStyle = "#fff"; g.font = `500 34px ${body}`;
  spaced(g, "ВАЙБОМЕТР", cx, 190, 9);
  g.textAlign = "right"; g.fillStyle = "rgba(255,255,255,.75)"; g.font = `600 22px ${body}`;
  ["РЯДОМ", "НА ОДНОЙ", "ВОЛНЕ"].forEach((t, i) => spaced(g, t, W - 60, 70 + i * 34, 5));
  g.textAlign = "center";

  // кольцо шкалы
  const ry = 790, R = 290, sw = 40;
  const a0 = Math.PI * 0.75, span = Math.PI * 1.5;
  const aEnd = a0 + span * Math.min(pct, 100) / 100;
  g.fillStyle = "rgba(7,6,13,.55)";
  g.beginPath(); g.arc(cx, ry, R + 38, 0, 2 * Math.PI); g.fill();
  g.lineWidth = sw; g.strokeStyle = "rgba(255,255,255,.12)";
  g.beginPath(); g.arc(cx, ry, R, a0, a0 + span); g.stroke();
  const grad = g.createLinearGradient(cx - R, ry + R, cx + R, ry - R);
  grad.addColorStop(0, "#ff7ac3"); grad.addColorStop(0.5, "#9b5cff"); grad.addColorStop(1, "#d9b3ff");
  g.strokeStyle = grad; g.shadowColor = "rgba(168,85,247,.9)"; g.shadowBlur = 44;
  g.beginPath(); g.arc(cx, ry, R, a0, aEnd); g.stroke(); g.shadowBlur = 0;
  g.fillStyle = "#fff"; g.shadowColor = "#fff"; g.shadowBlur = 24;
  g.beginPath(); g.arc(cx + R * Math.cos(aEnd), ry + R * Math.sin(aEnd), 17, 0, 2 * Math.PI); g.fill(); g.shadowBlur = 0;

  g.fillStyle = "rgba(255,255,255,.7)"; g.font = `500 30px ${body}`;
  spaced(g, "ВАШ ВАЙБ", cx, ry - 120, 9);
  g.fillStyle = "#fff"; g.font = `500 190px ${head}`;
  g.shadowColor = "rgba(255,61,154,.55)"; g.shadowBlur = 30;
  g.fillText(`${pct}`, cx - 28, ry + 80);
  const wNum = g.measureText(`${pct}`).width;
  g.font = `500 80px ${head}`; g.textAlign = "left";
  g.fillText("%", cx - 28 + wNum / 2 + 6, ry + 80); g.textAlign = "center"; g.shadowBlur = 0;
  // пульс
  g.strokeStyle = "#d9b3ff"; g.lineWidth = 5; g.lineJoin = "round";
  g.beginPath(); g.moveTo(cx - 60, ry + 170); g.lineTo(cx - 28, ry + 170); g.lineTo(cx - 14, ry + 140);
  g.lineTo(cx + 4, ry + 205); g.lineTo(cx + 18, ry + 165); g.lineTo(cx + 60, ry + 170); g.stroke();

  // имя и вердикт
  g.fillStyle = "#fff"; g.font = `500 70px ${body}`;
  spaced(g, `Я И ${name.toUpperCase()}`, cx, 1215, 8);
  g.fillStyle = "#b983ff"; g.font = `600 56px ${body}`;
  spaced(g, verdict.toUpperCase(), cx, 1310, 14);

  // сердца
  for (let i = 0; i < total; i++) {
    const hx = cx + (i - (total - 1) / 2) * 92;
    heartPath(g, hx, 1405, 30);
    if (i < matches) {
      const hg = g.createLinearGradient(hx - 30, 1380, hx + 30, 1440);
      hg.addColorStop(0, "#c084fc"); hg.addColorStop(1, "#ff7ac3");
      g.fillStyle = hg; g.shadowColor = "#b983ff"; g.shadowBlur = 22; g.fill(); g.shadowBlur = 0;
    } else {
      g.strokeStyle = "rgba(255,255,255,.6)"; g.lineWidth = 4; g.stroke();
    }
  }
  g.fillStyle = "rgba(255,255,255,.75)"; g.font = `500 34px ${body}`;
  spaced(g, `${matches} ИЗ ${total}`, cx, 1500, 8);
  g.strokeStyle = "rgba(255,255,255,.3)"; g.lineWidth = 2;
  g.beginPath(); g.moveTo(cx - 330, 1490); g.lineTo(cx - 140, 1490); g.moveTo(cx + 140, 1490); g.lineTo(cx + 330, 1490); g.stroke();

  // кнопка внизу
  const bw = 920, bh = 130, bx = (W - bw) / 2, by = 1650;
  const bgr = g.createLinearGradient(bx, 0, bx + bw, 0);
  bgr.addColorStop(0, "#5b3bd6"); bgr.addColorStop(1, "#b04ad8");
  g.fillStyle = "rgba(20,12,40,.85)"; g.beginPath(); g.roundRect(bx, by, bw, bh, 65); g.fill();
  g.lineWidth = 4; g.strokeStyle = bgr; g.shadowColor = "rgba(168,85,247,.8)"; g.shadowBlur = 30; g.stroke(); g.shadowBlur = 0;
  g.fillStyle = "#fff"; g.font = `600 38px ${body}`; g.textAlign = "center";
  g.fillText("Проверь вайб: @vibemeter_bot", cx, by + 80);
  g.strokeStyle = "#fff"; g.lineWidth = 5;
  g.beginPath(); g.moveTo(bx + bw - 110, by + 65); g.lineTo(bx + bw - 66, by + 65);
  g.moveTo(bx + bw - 86, by + 47); g.lineTo(bx + bw - 66, by + 65); g.lineTo(bx + bw - 86, by + 83); g.stroke();
  g.fillStyle = "#fff"; g.beginPath(); g.moveTo(bx + 70, by + 66); g.lineTo(bx + 125, by + 42); g.lineTo(bx + 108, by + 92);
  g.lineTo(bx + 94, by + 74); g.closePath(); g.fill();

  g.fillStyle = "rgba(255,255,255,.55)"; g.font = `500 22px ${body}`;
  spaced(g, "ТОЛЬКО 18+", cx, 1860, 6);
  return c;
}

// =========================================================
// Друзья, игры, онбординг
// =========================================================
function invite() {
  haptic("light");
  const link = `https://t.me/${state.me.bot_username || "vibemeter_bot"}?start=ref_${state.me.user.id}`;
  const text = "Залетай в Вайбометр: знакомства, где сначала вайб, а потом фото 💜";
  if (DEMO) {
    try { navigator.clipboard.writeText(link); } catch (_) {}
    toast("Ссылка скопирована");
    return;
  }
  tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`);
}

// =========================================================
// Игра «Что выберешь?» прямо в приложении
// =========================================================
const game = { data: { state: "idle" }, timer: null, busy: false, liked: false };

function stopGamePolling() { clearInterval(game.timer); game.timer = null; }

function startGamePolling() {
  stopGamePolling();
  game.timer = setInterval(async () => {
    if (route() !== "games") return stopGamePolling();
    if (!["waiting", "waiting_opponent"].includes(game.data.state) || game.busy) return;
    try { applyGame(await api.gameState()); } catch (_) {}
  }, 2500);
}

function applyGame(next) {
  const prev = game.data.state;
  game.data = next;
  if (next.state === "finished" && prev !== "finished") { game.liked = false; haptic("success"); }
  if (next.state === "playing" && prev === "waiting") haptic("medium");
  renderGame();
  if (["waiting", "waiting_opponent"].includes(next.state)) startGamePolling(); else stopGamePolling();
}

function gameVerdict(p) {
  if (p >= 80) return "💎 Редкое совпадение!";
  if (p >= 60) return "Хороший общий вайб 🙌";
  if (p >= 40) return "Кое-что общее точно есть";
  return "Вы довольно разные, и это тоже интересно";
}

function oppChip(o) {
  if (!o) return "";
  return `<div class="row" style="justify-content:center;gap:10px;margin-bottom:14px">
    <div class="avatar sm">${esc((o.name || "?")[0])}</div>
    <div><b>${esc(o.name)}, ${o.age}</b><div class="small muted">📍 ${esc(o.city || "")}</div></div></div>`;
}

function renderGame() {
  const root = $("#game-root");
  if (!root || duo.cur) return;
  const g = game.data;

  if (g.state === "idle") {
    root.innerHTML = `
      <div class="hero">
        <h2 style="max-width:none">🍭 Что выберешь?</h2>
        <p style="max-width:none">5 вопросов «то или это» с человеком на одной волне. В конце: процент совпадения и шанс на вайб</p>
        <button class="btn btn-fill" id="game-join">${svg("game")} Играть</button>
      </div>
      ${duoHome()}`;
    $("#game-join").onclick = joinGame;
    bindDuoHome(root);
  }

  if (g.state === "waiting") {
    root.innerHTML = `
      <div class="card strong" style="text-align:center;padding:26px 16px">
        ${gauge(60, 150, "ищем пару")}
        <h2 style="font-family:var(--head);font-size:17px;margin:14px 0 6px">Ищем тебе пару для игры</h2>
        <p class="muted small" style="margin:0 auto 16px;max-width:280px">Можно закрыть приложение: как только найдём человека, бот пришлёт сообщение</p>
        <button class="btn btn-ghost btn-sm" id="game-leave">Отменить</button>
      </div>`;
    animateGauges(root);
    $("#game-leave").onclick = leaveGame;
    // стрелка шкалы «ищет»: плавно ходит туда-сюда
    const needle = $(".gauge .needle", root);
    if (needle) { let t = 0; const id = setInterval(() => { if (!$(".gauge .needle")) return clearInterval(id); t += 1; needle.style.transform = `rotate(${-90 + 180 * (0.5 + 0.45 * Math.sin(t / 2))}deg)`; }, 500); }
  }

  if (g.state === "playing") {
    const q = g.question;
    const dots = Array.from({ length: g.total }, (_, i) => `<i class="${i < q.index ? "done" : i === q.index ? "on" : ""}"></i>`).join("");
    root.innerHTML = `
      ${oppChip(g.opponent)}
      <div class="game-dots">${dots}</div>
      <p class="label" style="text-align:center;margin:16px 0 6px">Вопрос ${q.index + 1} из ${g.total}</p>
      <h2 class="game-q">${esc(q.text)}</h2>
      <div class="list" style="gap:12px">
        <button class="game-opt" data-ans="a"><span>${esc(q.a)}</span></button>
        <div class="game-or">или</div>
        <button class="game-opt" data-ans="b"><span>${esc(q.b)}</span></button>
      </div>`;
    $$("[data-ans]", root).forEach((b) => b.onclick = () => answerGame(b, q.index));
  }

  if (g.state === "waiting_opponent") {
    root.innerHTML = `
      <div class="card strong" style="text-align:center;padding:26px 16px">
        ${oppChip(g.opponent)}
        ${gauge(80, 130, "ты закончил")}
        <h2 style="font-family:var(--head);font-size:17px;margin:14px 0 6px">Ждём ${esc(g.opponent ? g.opponent.name : "соперника")}</h2>
        <p class="muted small" style="margin:0 auto 6px;max-width:280px">Как только ответит, покажем, насколько вы совпали. Бот напомнит</p>
        ${g.stuck ? `<button class="btn btn-violet btn-sm mt" id="game-join">Найти другого</button>` : ""}
      </div>`;
    animateGauges(root);
    const j = $("#game-join"); if (j) j.onclick = joinGame;
  }

  if (g.state === "finished") {
    root.innerHTML = `
      <div class="card strong" style="text-align:center;padding:24px 16px">
        ${oppChip(g.opponent)}
        <div style="display:flex;justify-content:center">${gauge(g.percentage, 180, "совпадение")}</div>
        <h2 style="font-family:var(--head);font-size:18px;margin:16px 0 4px">${gameVerdict(g.percentage)}</h2>
        <p class="muted" style="margin:0">Совпали в ${g.matches} из ${g.total} вопросов</p>
        <div class="grid g2 mt-l">
          <button class="btn btn-pink" id="game-like" ${game.liked ? "disabled" : ""}>${svg("heart")} ${game.liked ? "Отправлено" : "Вайб"}</button>
          <button class="btn btn-violet" id="game-join">${svg("game")} Ещё раз</button>
        </div>
        <button class="btn btn-ghost mt" id="game-share" style="width:100%">${svg("share")} Картинка для сторис</button>
      </div>`;
    animateGauges(root);
    $("#game-join").onclick = joinGame;
    $("#game-like").onclick = likeOpponent;
    $("#game-share").onclick = shareGameCard;
  }
}

async function shareGameCard() {
  const g = game.data;
  const btn = $("#game-share");
  if (btn) btn.disabled = true;
  haptic("medium");
  try {
    const canvas = await drawShareCard({
      pct: g.percentage, name: (g.opponent && g.opponent.name) || "незнакомцем",
      matches: g.matches, total: g.total, verdict: vibeWord(g.percentage),
    });
    const blob = await new Promise((res) => canvas.toBlob(res, "image/png"));
    if (DEMO) { toast("Картинка готова (в демо не отправляется)"); }
    else if (tg.shareToStory && tg.isVersionAtLeast && tg.isVersionAtLeast("7.8")) {
      // сразу открываем редактор сторис Telegram
      const { url, link } = await api.story(blob);
      tg.shareToStory(url, { text: "Мы совпали! Проверь свой вайб", widget_link: { url: link, name: "Проверь вайб" } });
    } else {
      await api.shareCard(blob);
      toast("Картинка пришла в чат с ботом");
    }
  } catch (e) { toast(errorText(e)); }
  if (btn) btn.disabled = false;
}

async function joinGame() {
  if (game.busy) return;
  game.busy = true; haptic("medium");
  try { applyGame(await api.gameJoin()); } catch (e) { toast(errorText(e)); }
  game.busy = false;
}

async function leaveGame() {
  try { await api.gameLeave(); } catch (_) {}
  applyGame({ state: "idle" });
}

async function answerGame(btn, index) {
  if (game.busy) return;
  game.busy = true; haptic("light");
  btn.classList.add("picked");
  $$(".game-opt").forEach((b) => b.disabled = true);
  try {
    const next = await api.gameAnswer(game.data.game_id, index, btn.dataset.ans);
    game.busy = false;
    applyGame(next);
  } catch (e) {
    game.busy = false;
    toast(e.code === "rejected" ? "Этот вопрос уже отвечен" : errorText(e));
    try { applyGame(await api.gameState()); } catch (_) {}
  }
}

async function likeOpponent() {
  const o = game.data.opponent;
  if (!o || game.liked) return;
  game.liked = true; renderGame(); haptic("medium");
  try {
    const res = await api.vibe(o.id, "like");
    if (res.mutual) { showMatch(res.match || o); refreshSoft(); }
    else toast("Вайб отправлен 💜");
  } catch (e) { game.liked = false; renderGame(); toast(errorText(e)); }
}

// =========================================================
// Игры на двоих: «Правда или действие» и «Викторина вайба»
// =========================================================
const duo = { list: [], cur: null, timer: null, busy: false };
const DUO_KINDS = {
  truth_dare: { icon: "🔥", title: "Правда или действие", hint: "Вопросы и задания по очереди. Только с теми, у кого взаимно" },
  quiz: { icon: "🎯", title: "Викторина вайба", hint: "Один отвечает про себя, второй угадывает" },
};

function duoHome() {
  const active = duo.list.filter((d) => d.status === "active");
  const mine = active.filter((d) => d.my_turn);
  const rows = (list) => list.map((d) => `
    <button class="game" data-duo-open="${d.id}" style="text-align:left;width:100%">
      <div class="gi">${DUO_KINDS[d.kind].icon}</div>
      <div class="grow"><b>${esc(d.title)} · ${esc(d.partner.name)}</b><small>${d.my_turn ? "Твой ход" : "Ждём ответ"}</small></div>
      ${d.my_turn ? `<span class="badge" style="position:static">!</span>` : svg("chev", "chev")}
    </button>`).join("");
  const kinds = Object.entries(DUO_KINDS).map(([k, v]) => `
    <button class="game" data-duo-kind="${k}" style="text-align:left;width:100%">
      <div class="gi">${v.icon}</div><div class="grow"><b>${v.title}</b><small>${v.hint}</small></div>${svg("chev", "chev")}
    </button>`).join("");
  return `
    ${active.length ? `<p class="label mt-l">Твои игры${mine.length ? ` · ходов ждут: ${mine.length}` : ""}</p><div class="list">${rows(active)}</div>` : ""}
    <p class="label mt-l">С людьми, у кого взаимно</p>
    <div class="list">${kinds}</div>`;
}

function bindDuoHome(root) {
  $$("[data-duo-open]", root).forEach((b) => b.onclick = () => openDuo(Number(b.dataset.duoOpen)));
  $$("[data-duo-kind]", root).forEach((b) => b.onclick = () => pickPartner(b.dataset.duoKind));
}

function pickPartner(kind) {
  haptic("select");
  const people = state.vibes.mutual;
  if (!people.length) {
    openSheet(`<h2 style="font-family:var(--head);font-size:17px;margin:4px 0 8px">${DUO_KINDS[kind].title}</h2>
      <p class="muted" style="margin:0 0 14px">Эта игра для пар, где вайб взаимный. Лайкай анкеты, и первый партнёр скоро появится</p>
      <button class="btn btn-fill" data-close>Понятно</button>`);
    return;
  }
  const sheet = openSheet(`<h2 style="font-family:var(--head);font-size:17px;margin:4px 0 12px">С кем играем?</h2>
    <div class="list">${people.map((p) => `<button class="person" data-duo-with="${p.id}" style="width:100%;text-align:left">
      ${avatarFor(p, "pink")}<div class="grow"><b>${esc(p.name)}, ${p.age}</b><small>📍 ${esc(p.city || "")}</small></div>${svg("chev", "chev")}</button>`).join("")}</div>`);
  people.forEach(withPhoto);
  $$("[data-duo-with]", sheet).forEach((b) => b.onclick = async () => {
    closeSheet();
    try { openDuoData(await api.duoStart(kind, Number(b.dataset.duoWith))); } catch (e) { toast(errorText(e)); }
  });
}

async function openDuo(id) {
  try { openDuoData(await api.duoState(id)); } catch (e) { toast(errorText(e)); }
}

function openDuoData(data) {
  duo.cur = data;
  renderDuo();
  startDuoPolling();
}

function stopDuoPolling() { clearInterval(duo.timer); duo.timer = null; }
function startDuoPolling() {
  stopDuoPolling();
  duo.timer = setInterval(async () => {
    if (route() !== "games" || !duo.cur || duo.busy) return stopDuoPolling();
    if (duo.cur.my_turn) return;
    try {
      const next = await api.duoState(duo.cur.id);
      const before = JSON.stringify(duo.cur.view);
      duo.cur = next;
      if (JSON.stringify(next.view) !== before) { haptic("light"); renderDuo(); }
    } catch (_) {}
  }, 3000);
}

function closeDuo() {
  stopDuoPolling();
  duo.cur = null;
  openGames();
}

async function duoAct(body) {
  if (duo.busy || !duo.cur) return;
  duo.busy = true; haptic("medium");
  try {
    duo.cur = await api.duoAct(duo.cur.id, body);
    renderDuo();
  } catch (e) { toast(errorText(e)); }
  duo.busy = false;
}

function duoWait(text) {
  return `<div class="card strong" style="text-align:center;padding:24px 16px"><div style="font-size:30px">⏳</div>
    <p class="muted" style="margin:10px auto 0;max-width:280px">${text}</p></div>`;
}

function renderDuo() {
  const root = $("#game-root");
  if (!root || !duo.cur) return;
  const d = duo.cur, v = d.view, p = d.partner;
  const name = esc(p.name);
  const head = `<button class="btn btn-ghost btn-sm" id="duo-back" style="margin-bottom:12px">← К играм</button>${oppChip(p)}`;
  let body = "";

  if (d.kind === "truth_dare") {
    const prog = `<p class="label" style="text-align:center;margin:0 0 10px">Раунд ${Math.min(v.round + 1, v.rounds)} из ${v.rounds}</p>`;
    if (v.phase === "choose") {
      body = v.my_turn
        ? `${prog}<h2 class="game-q">Твой ход. Что выбираешь?</h2>
           <div class="list" style="gap:12px"><button class="game-opt" data-pick="truth"><span>💬 Правда</span></button><div class="game-or">или</div><button class="game-opt" data-pick="dare"><span>🔥 Действие</span></button></div>`
        : prog + duoWait(`${name} выбирает: правду или действие`);
    } else if (v.phase === "answer") {
      body = v.my_turn
        ? `${prog}<div class="card strong"><p class="label">${v.pick === "truth" ? "Правда" : "Действие"}</p>
            <h2 class="game-q" style="margin-bottom:12px">${esc(v.prompt)}</h2>
            <textarea class="field" id="duo-text" rows="3" maxlength="300" placeholder="${v.pick === "truth" ? "Твой честный ответ" : "Что ты сделал(а)? Опиши в паре слов"}"></textarea></div>
           <div class="grid g2 mt"><button class="btn btn-ghost" id="duo-skip">Пропустить</button><button class="btn btn-fill" id="duo-send">Отправить</button></div>`
        : prog + `<div class="card"><p class="label">${v.pick === "truth" ? "Правда" : "Действие"} для ${name}</p><p style="margin:0">${esc(v.prompt)}</p></div>` + duoWait(`${name} отвечает`);
    } else if (v.phase === "rate") {
      body = !v.my_turn
        ? `${prog}<div class="card strong"><p class="label">${v.pick === "truth" ? "Правда" : "Действие"}</p><p style="margin:0 0 12px"><b>${esc(v.prompt)}</b></p>
            <div class="bubble">${v.answer ? esc(v.answer) : "<i class='muted'>Пропустил(а)</i>"}</div></div>
           <div class="grid g2 mt"><button class="btn btn-ghost" data-rate="ok">👌 Ок</button><button class="btn btn-pink" data-rate="fire">🔥 Огонь</button></div>`
        : prog + duoWait(`${name} оценивает твой ответ`);
    } else {
      body = `<div class="card strong" style="text-align:center"><div style="font-size:34px">🎉</div><h2 class="game-q" style="margin:6px 0">Игра окончена</h2>
          <p class="muted" style="margin:0">${v.log.length} ходов. Вот что вы пережили</p></div>
        <div class="list mt">${v.log.map((x) => `<div class="card"><p class="label">${x.mine ? "Ты" : name} · ${x.pick === "truth" ? "правда" : "действие"} ${x.score === "fire" ? "🔥" : "👌"}</p>
          <p style="margin:0 0 6px"><b>${esc(x.prompt)}</b></p><p class="muted" style="margin:0">${x.answer ? esc(x.answer) : "Пропущено"}</p></div>`).join("")}</div>
        <div class="grid g2 mt"><button class="btn btn-ghost" id="duo-again">Ещё раз</button><button class="btn btn-pink" id="duo-write">${svg("chat")} Написать</button></div>`;
    }
  } else {
    const q = v.question;
    const opts = q ? `<h2 class="game-q">${esc(q.q)}</h2><div class="list" style="gap:12px"><button class="game-opt" data-ans="a"><span>${esc(q.a)}</span></button><div class="game-or">или</div><button class="game-opt" data-ans="b"><span>${esc(q.b)}</span></button></div>` : "";
    const dots = (n) => `<div class="game-dots">${Array.from({ length: v.total }, (_, i) => `<i class="${i < n ? "done" : i === n ? "on" : ""}"></i>`).join("")}</div>`;
    if (v.phase === "answer") body = `${dots(v.index)}<p class="label" style="text-align:center;margin:14px 0 6px">Отвечай про себя, честно · ${v.index + 1} из ${v.total}</p>${opts}`;
    else if (v.phase === "wait_author") body = duoWait(`${name} отвечает на 5 вопросов про себя. Потом ты будешь угадывать`);
    else if (v.phase === "guess") body = `${dots(v.index)}<p class="label" style="text-align:center;margin:14px 0 6px">Как ответил(а) ${name}? · ${v.index + 1} из ${v.total}</p>${opts}`;
    else if (v.phase === "wait_guess") body = duoWait(`${name} угадывает твои ответы. Результат придёт сюда`);
    else body = `<div class="card strong" style="text-align:center;padding:24px 16px"><div style="display:flex;justify-content:center">${gauge(v.percentage, 170, "знаете друг друга")}</div>
        <h2 class="game-q" style="margin:14px 0 4px">${v.percentage >= 80 ? "Вы читаете друг друга" : v.percentage >= 60 ? "Неплохо знаете друг друга" : v.percentage >= 40 ? "Есть что узнать" : "Вы загадка друг для друга"}</h2>
        <p class="muted" style="margin:0">Угадано ${v.matches} из ${v.total}</p></div>
      <div class="list mt">${v.items.map((it) => `<div class="card"><p style="margin:0 0 6px"><b>${esc(it.q)}</b></p>
        <p class="muted small" style="margin:0">${v.i_am_author ? "Ты ответил(а)" : name + " ответил(а)"}: <b>${esc(it[it.self])}</b> · ${v.i_am_author ? name + " думал(а)" : "ты думал(а)"}: <b>${esc(it[it.guess])}</b> ${it.self === it.guess ? "✅" : "❌"}</p></div>`).join("")}</div>
      <div class="grid g2 mt"><button class="btn btn-ghost" id="duo-again">Поменяться ролями</button><button class="btn btn-pink" id="duo-write">${svg("chat")} Написать</button></div>`;
  }

  root.innerHTML = head + body;
  if (v.phase === "done") animateGauges(root);
  $("#duo-back").onclick = closeDuo;
  $$("[data-pick]", root).forEach((b) => b.onclick = () => duoAct({ action: "choose", pick: b.dataset.pick }));
  $$("[data-rate]", root).forEach((b) => b.onclick = () => duoAct({ action: "rate", score: b.dataset.rate }));
  $$("[data-ans]", root).forEach((b) => b.onclick = () => duoAct({ action: "answer", answer: b.dataset.ans }));
  const send = $("#duo-send"), skip = $("#duo-skip");
  if (send) send.onclick = () => {
    const t = $("#duo-text").value.trim();
    if (!t) { toast("Напиши ответ"); return; }
    duoAct({ action: "answer", text: t });
  };
  if (skip) skip.onclick = () => duoAct({ action: "skip" });
  const again = $("#duo-again"), write = $("#duo-write");
  if (again) again.onclick = async () => { try { openDuoData(await api.duoStart(d.kind, p.id)); } catch (e) { toast(errorText(e)); } };
  if (write) write.onclick = () => writeTo(p);
}
async function openGames() {
  stopGamePolling();
  stopDuoPolling();
  duo.cur = null;
  renderGame();
  try { duo.list = (await api.duoList()).games; } catch (_) { duo.list = []; }
  try { applyGame(await api.gameState()); } catch (_) { applyGame({ state: "idle" }); }
}

const ONB = [
  () => `<div class="onb-logo">${brandMark()}<span class="wordmark">Вайбометр</span></div>
    <div class="onb-slogan">Твой круг. Твой вайб.</div>
    <p style="margin-top:18px">Знакомства, где сначала совпадает вайб, а уже потом — внешность</p>`,
  () => `<div class="mini-card"><div class="aura" style="--a1:#b04cff;--a2:#ff3d9a"><div class="silhouette">А</div><div class="lock-note">${svg("lock")} Фото скрыто</div></div><div class="pname">Анастасия, 19</div></div>
    <h1>Без фото. Только вайб</h1>
    <p>Смотришь на интересы, город и «о себе». Шкала показывает, насколько вы на одной волне</p>`,
  () => `${gauge(87, 170, "вайб")}
    <h1>Совпало — фото открыто</h1>
    <p>Свайп вправо — вайб, влево — дальше. Если вайб взаимный, вы видите фото друг друга и можете написать</p>`,
];

function showOnboarding() {
  const box = $("#onb");
  let i = 0;
  const draw = () => {
    box.innerHTML = `<div class="bg"></div>
      <button class="onb-skip" id="onb-skip">${i < ONB.length - 1 ? "Пропустить" : ""}</button>
      <div class="onb-slide">${ONB[i]()}</div>
      <div class="onb-dots">${ONB.map((_, k) => `<i class="${k === i ? "on" : ""}"></i>`).join("")}</div>
      <button class="btn btn-fill btn-block" id="onb-next" style="position:relative">${i < ONB.length - 1 ? "Дальше" : "Погнали 🚀"}</button>`;
    animateGauges(box);
    $("#onb-next").onclick = () => { haptic("light"); if (++i < ONB.length) draw(); else finish(); };
    $("#onb-skip").onclick = finish;
  };
  const finish = () => { store.set("vm_onb", "1"); box.classList.add("hidden"); };
  box.classList.remove("hidden");
  draw();
}

// =========================================================
// Рендер
// =========================================================
function errorText(e) {
  if (e && e.code === "banned") return "Аккаунт заблокирован";
  if (e && e.code === "network") return "Нет связи, проверь интернет";
  if (e && e.code === "not_found") return "Анкета уже недоступна";
  return "Не получилось, попробуй ещё раз";
}

function errorHtml(e) {
  const code = e && e.code;
  if (code === "banned") return emptyHtml("🚫", "Аккаунт заблокирован", "За нарушение правил Вайбометра");
  if (code === "no_profile") return `${emptyHtml("📝", "Сначала анкета", "Заполни её в чате с ботом: напиши /start, это минута")}
    <div style="text-align:center"><button class="btn btn-violet" onclick="tg && tg.close()">Открыть бота</button></div>`;
  if (code === "bad_init_data") return emptyHtml("⏳", "Сессия устарела", "Закрой и снова открой Вайбометр из бота");
  return `${emptyHtml("📡", "Нет связи", "Не получилось загрузить. Проверь интернет и попробуй ещё раз")}
    <div style="text-align:center"><button class="btn btn-violet" onclick="boot()">Повторить</button></div>`;
}

async function refreshSoft() {
  try {
    const [me, vibes] = await Promise.all([api.me(), api.vibes()]);
    state.me = me; state.vibes = vibes;
    renderChrome();
  } catch (_) {}
}

function render() {
  if (!state.me) return;
  stopGamePolling();
  stopDuoPolling();
  let r = route();
  if (!screens[r]) r = "home";
  if (r !== "edit") state.form = null;
  const v = view();
  v.innerHTML = screens[r]();
  v.classList.remove("enter"); void v.offsetWidth; v.classList.add("enter");
  window.scrollTo(0, 0);
  renderChrome();
  animateGauges(v);
  if (tg && tg.BackButton) (r === "home" ? tg.BackButton.hide() : tg.BackButton.show());

  $$("#invite-btn").forEach((b) => b.onclick = invite);
  $$("[data-daily]").forEach((b) => b.onclick = async () => {
    haptic("select");
    try {
      await api.daily(b.dataset.daily);
      state.me.daily.answer = b.dataset.daily;
      render();
    } catch (e) { toast(errorText(e)); }
  });
  $$("[data-sg]").forEach((b) => b.onclick = async () => {
    haptic("select");
    try {
      await api.saveProfile({ search_gender: b.dataset.sg });
      state.me.user.search_gender = b.dataset.sg;
      state.lastSkip = null;
      render();
    } catch (e) { toast(errorText(e)); }
  });

  if (r === "search") {
    loadCandidate();
    $("#btn-like").onclick = () => decide("like");
    $("#btn-skip").onclick = () => decide("skip");
    $("#btn-question").onclick = () => state.candidate && openQuestion(state.candidate);
  }
  if (r === "vibes") {
    $$("[data-vt]").forEach((b) => b.onclick = () => { state.vibesTab = b.dataset.vt; haptic("select"); render(); });
    $$("[data-write]").forEach((b) => b.onclick = () => writeTo(state.vibes.mutual.find((p) => String(p.id) === b.dataset.write)));
    $$("[data-in-like]").forEach((b) => b.onclick = (e) => { e.stopPropagation(); incomingAction(Number(b.dataset.inLike), "like"); });
    $$("[data-in-skip]").forEach((b) => b.onclick = (e) => { e.stopPropagation(); incomingAction(Number(b.dataset.inSkip), "skip"); });
    $$("[data-details]").forEach((row) => row.onclick = () => openDetails(state.vibes.incoming.find((p) => String(p.id) === row.dataset.details), "vibes"));
    state.vibes.mutual.forEach(withPhoto);
  }
  if (r === "games") openGames();
  if (r === "profile") bindPhotoButton();
  if (r === "edit") { bindEdit(); bindPhotoButton(); }
  if (r === "fame") $$("[data-fame]").forEach((b) => b.onclick = () => { state.fameFilter = b.dataset.fame; haptic("select"); render(); });
  if (r === "settings") {
    $("#set-edit").onclick = () => go("edit");
    $("#set-onb").onclick = showOnboarding;
    $("#set-invite").onclick = invite;
    $("#set-privacy").onclick = openPrivacy;
    $("#set-bot").onclick = () => { toast("Открой чат с ботом → ⚙️ Настройки"); if (!DEMO) setTimeout(() => tg.close(), 1400); };
  }
}

if (tg && tg.BackButton) tg.BackButton.onClick(() => {
  if (!$("#onb").classList.contains("hidden")) return;
  if (sheetOpen()) return closeSheet();
  if (!$("#overlay").classList.contains("hidden")) return $("#overlay").classList.add("hidden");
  if (history.length > 1) history.back(); else go("home");
});

async function boot() {
  if (DEMO && !$(".demo")) document.body.insertAdjacentHTML("beforeend", '<div class="demo">демо-режим</div>');
  view().innerHTML = `<div class="empty" style="padding-top:80px">${gauge(72, 140, "загружаем вайб")}</div>`;
  animateGauges(view());
  try {
    const [me, vibes] = await Promise.all([api.me(), api.vibes()]);
    state.me = me; state.vibes = vibes;
    render();
    withPhoto(me.user);
    if (!store.get("vm_onb")) showOnboarding();
  } catch (e) {
    view().innerHTML = errorHtml(e);
  }
}

boot();
