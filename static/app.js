// CineScope frontend 🎬 - genre browse, theme change, watchlist (browser lo save)
const state = { kind: "movie", genre: null, lang: null, genres: {}, view: "browse", wlKind: "all" };
const WL_KEY = "cinescope.watchlist";
const DEFAULT_THEME = { bg: "#0e1116", surface: "#1a1f27", accent: "#e50914", text: "#f2f2f2" };

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

// ---------------- theme 🎨 ----------------
function applyTheme(t) {
  const root = document.documentElement.style;
  for (const [k, v] of Object.entries(t || DEFAULT_THEME)) root.setProperty(`--${k}`, v);
}

// ---------------- watchlist (localStorage) 📝 ----------------
function loadWL() {
  try { return JSON.parse(localStorage.getItem(WL_KEY)) || []; } catch { return []; }
}
function saveWL(list) {
  try { localStorage.setItem(WL_KEY, JSON.stringify(list)); } catch { /* private mode - memory lo matrame */ }
  state.wl = list;
  $("#wl-count").textContent = list.length;
}
const inWL = (id) => (state.wl || []).some((x) => x.id === id);

function toggleWL(item) {
  let list = loadWL();
  if (list.some((x) => x.id === item.id)) {
    list = list.filter((x) => x.id !== item.id);
    toast(`Removed "${item.title}"`);
  } else {
    const { id, title, kind, genres, emoji, year, rating, rating_src, poster } = item;
    list.unshift({ id, title, kind, genres, emoji, year, rating, rating_src, poster, watched: false, added: Date.now() });
    toast(`Added "${item.title}" to watchlist ✅`);
  }
  saveWL(list);
  document.querySelectorAll(`[data-add="${CSS.escape(item.id)}"]`).forEach((b) => setAddBtn(b, inWL(item.id)));
  refreshForYou();
}
function setAddBtn(btn, on) {
  btn.classList.toggle("on", on);
  btn.textContent = on ? "✓" : "+";
  btn.title = on ? "In your watchlist" : "Add to watchlist";
}

let toastTimer;
function toast(msg) {
  let t = $(".toast");
  if (!t) { t = document.createElement("div"); t.className = "toast"; document.body.appendChild(t); }
  t.textContent = msg; t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.hidden = true), 1800);
}

// ---------------- cards & rows 🃏 ----------------
function genreColor(item) {
  const g = state.genres[item.genres?.[0]];
  return g ? g.theme.accent : "#555";
}

const stars = (x) => (x.rating ? ` · ⭐ ${x.rating}` : x.imdb ? ` · ⭐ ${x.imdb}` : "");

function cardEl(item) {
  const el = document.createElement("div");
  el.className = "card" + (item.poster ? " has-poster" : "");
  el.tabIndex = 0;
  el.style.setProperty("--g", genreColor(item));
  const tag = item.language && item.india ? `🇮🇳 ${esc(item.language)}` : item.india ? "🇮🇳 India" : "";
  el.innerHTML = `
    ${item.poster ? `<img class="poster" loading="lazy" alt="" src="${esc(item.poster)}">` : ""}
    ${tag ? `<span class="tag">${tag}</span>` : ""}
    <button class="add" data-add="${esc(item.id)}" aria-label="Add to watchlist"></button>
    <div class="emoji">${item.emoji}</div>
    <div class="title">${esc(item.title)}</div>
    <div class="meta">${item.year}${stars(item)} · ${esc(item.genre_labels.slice(0, 2).join(", "))}</div>`;
  // Poster load avvakapothe emoji card ki fallback 🎭
  const img = $(".poster", el);
  if (img) img.onerror = () => { img.remove(); el.classList.remove("has-poster"); };
  const add = $(".add", el);
  setAddBtn(add, inWL(item.id));
  add.addEventListener("click", (e) => { e.stopPropagation(); toggleWL(item); });
  el.addEventListener("click", () => openModal(item.id));
  el.addEventListener("keydown", (e) => { if (e.key === "Enter") openModal(item.id); });
  return el;
}

function rowEl(row) {
  const sec = document.createElement("section");
  sec.className = "row";
  sec.id = `row-${row.key}`;
  sec.innerHTML = `
    <div class="row-head"><h2>${row.emoji} ${esc(row.title)}</h2>
      ${row.count ? `<span class="count muted">${row.count} titles</span>` : ""}</div>
    <div class="row-wrap">
      <button class="arrow left" aria-label="Scroll left">‹</button>
      <div class="track"></div>
      <button class="arrow right" aria-label="Scroll right">›</button>
    </div>`;
  const track = $(".track", sec);
  row.items.forEach((it) => track.appendChild(cardEl(it)));
  $(".arrow.left", sec).onclick = () => track.scrollBy({ left: -track.clientWidth * 0.8 });
  $(".arrow.right", sec).onclick = () => track.scrollBy({ left: track.clientWidth * 0.8 });
  return sec;
}

// ---------------- browse 🔍 ----------------
function renderChips() {
  const box = $("#genre-chips");
  box.innerHTML = "";
  const all = document.createElement("button");
  all.className = "chip" + (state.genre ? "" : " active");
  all.textContent = "✨ All";
  all.onclick = () => { $("#search").value = ""; setGenre(null); };
  box.appendChild(all);
  Object.values(state.genres).forEach((g) => {
    const b = document.createElement("button");
    b.className = "chip" + (state.genre === g.key ? " active" : "");
    b.textContent = `${g.emoji} ${g.label}`;
    b.onclick = () => { $("#search").value = ""; setGenre(g.key); };
    box.appendChild(b);
  });
}

function setGenre(key) {
  state.genre = key;
  $("#search-results").innerHTML = "";
  applyTheme(key ? state.genres[key].theme : DEFAULT_THEME);
  renderChips();
  loadBrowse();
}

async function loadBrowse() {
  const params = new URLSearchParams({ kind: state.kind });
  if (state.genre) params.set("genre", state.genre);
  if (state.lang) params.set("lang", state.lang);
  $("#rows").innerHTML = '<p class="muted">Loading…</p>';
  const data = await api(`/api/browse?${params}`);
  const kindLabel = (data.language ? data.language + " " : "") + (state.kind === "movie" ? "Movies" : "Web Series");
  const hero = $("#hero");
  if (data.genre) {
    hero.innerHTML = `
      <h1><span class="big">${data.genre.emoji}</span>${esc(data.genre.label)} ${kindLabel}</h1>
      <div class="muted">${data.total} titles · ${data.subgenres.length} sub-genres</div>
      <div class="subs">${data.subgenres.map((s) =>
        `<button class="chip" data-jump="${esc(s.key)}">${s.emoji} ${esc(s.title)} <span class="muted">${s.count}</span></button>`).join("")}</div>`;
    hero.querySelectorAll("[data-jump]").forEach((b) =>
      (b.onclick = () => document.getElementById(`row-${b.dataset.jump}`)?.scrollIntoView({ behavior: "smooth" })));
  } else {
    hero.innerHTML = `<h1><span class="big">🍿</span>All ${kindLabel}</h1>
      <div class="muted">${data.total} titles · pick a genre to change the whole vibe</div>`;
  }
  const rows = $("#rows");
  rows.innerHTML = "";
  data.rows.forEach((r) => rows.appendChild(rowEl(r)));
  if (data.subgenres.length) {
    const h = document.createElement("h2");
    h.style.margin = "34px 0 0";
    h.textContent = data.genre ? `${data.genre.emoji} Sub-genres` : "🎭 By genre";
    rows.appendChild(h);
    data.subgenres.forEach((r) => rows.appendChild(rowEl(r)));
  }
  refreshForYou();
}

async function refreshForYou() {
  const box = $("#for-you");
  const wl = loadWL();
  if (!wl.length || state.view !== "browse") { box.innerHTML = ""; return; }
  try {
    const recs = await api("/api/recommend", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: wl.slice(0, 30).map((x) => x.id), kind: state.kind, genre: state.genre }),
    });
    box.innerHTML = "";
    const g = state.genre && state.genres[state.genre];
    const title = g ? `${g.label} picks based on your watchlist` : "Because of your watchlist";
    if (recs.length) box.appendChild(rowEl({ key: "for-you", emoji: g ? g.emoji : "🍿", title, items: recs }));
  } catch { box.innerHTML = ""; }
}

// ---------------- search ⌨️ ----------------
let searchTimer;
$("#search").addEventListener("input", (e) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => runSearch(e.target.value.trim()), 300);
});

async function runSearch(q) {
  const box = $("#search-results");
  if (!q) { box.innerHTML = ""; return; }
  showView("browse");
  const res = await api(`/api/search?q=${encodeURIComponent(q)}`);
  // "action" ani type chesthe direct ga Action genre ki velli theme marchestham 🔴
  if (res.genre && res.genre.key !== state.genre) setGenre(res.genre.key);
  box.innerHTML = "";
  if (res.results.length) {
    box.appendChild(rowEl({ key: "search", emoji: "🔎", title: `Titles matching "${q}"`, items: res.results }));
  } else if (!res.genre) {
    box.innerHTML = `<p class="empty">No titles match "${esc(q)}". Try a genre like <b>action</b> or <b>romance</b>.</p>`;
  }
}

// ---------------- modal 🪟 ----------------
async function openModal(id) {
  const t = await api(`/api/title/${encodeURIComponent(id)}`);
  const color = genreColor(t);
  const len = t.kind === "series" ? (t.seasons ? `${t.seasons} season${t.seasons > 1 ? "s" : ""}` : "")
                                  : (t.runtime ? `${t.runtime} min` : "");
  $("#modal-body").innerHTML = `
    <div class="m-top">
      ${t.poster ? `<img class="m-poster" alt="${esc(t.title)} poster" src="${esc(t.poster)}">`
                 : `<div class="m-emoji" style="background:linear-gradient(160deg, ${color}, #000)">${t.emoji}</div>`}
      <div>
        <h2 class="m-title" id="m-title">${esc(t.title)}</h2>
        <div class="muted">${t.kind === "series" ? "📺 Web Series" : "🎬 Movie"} · ${t.year}${len ? " · " + len : ""}${t.age ? " · " + esc(t.age) : ""}${t.rating ? ` · ⭐ ${t.rating} ${esc(t.rating_src)}` : ""}${t.language ? " · 🗣️ " + esc(t.language) : ""}${t.india ? " · 🇮🇳 India" : ""}</div>
        <div style="margin:10px 0">${t.genre_labels.map((g) => `<span class="pill">${esc(g)}</span>`).join("")}</div>
        <p>${esc(t.description) || '<span class="muted">No description available.</span>'}</p>
        <button class="btn" id="m-add"></button>
      </div>
    </div>
    <div id="m-similar"></div>`;
  const add = $("#m-add");
  const paint = () => { add.textContent = inWL(t.id) ? "✓ In your watchlist" : "+ Add to watchlist"; add.className = inWL(t.id) ? "btn ghost" : "btn"; };
  paint();
  add.onclick = () => { toggleWL(t); paint(); };
  if (t.similar.length) $("#m-similar").appendChild(rowEl({ key: "similar", emoji: "🎯", title: "More like this", items: t.similar }));
  $("#modal").hidden = false;
}
$("#modal").addEventListener("click", (e) => { if (e.target.id === "modal" || e.target.closest(".close")) $("#modal").hidden = true; });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("#modal").hidden = true; });

// ---------------- watchlist view ✅ ----------------
function renderWatchlist() {
  const all = loadWL();
  const g = $("#wl-genre").value;
  const hide = $("#wl-hide-watched").checked;
  const list = all.filter((x) => (state.wlKind === "all" || x.kind === state.wlKind)
    && (!g || x.genres.includes(g)) && (!hide || !x.watched));
  const done = all.filter((x) => x.watched).length;
  $("#wl-progress").textContent = all.length ? `${done} of ${all.length} watched 🎉` : "";

  const ul = $("#wl-list");
  ul.innerHTML = "";
  if (!all.length) {
    ul.innerHTML = `<li class="empty">Your watchlist is empty. Tap <b>+</b> on any title to add it.</li>`;
  } else if (!list.length) {
    ul.innerHTML = `<li class="empty">Nothing matches these filters.</li>`;
  }
  // To-watch mundu, watched venaka
  list.sort((a, b) => a.watched - b.watched || b.added - a.added).forEach((x) => {
    const li = document.createElement("li");
    li.className = "wl-item" + (x.watched ? " done" : "");
    const labels = x.genres.map((k) => state.genres[k]?.label || k).join(", ");
    li.innerHTML = `
      <input type="checkbox" ${x.watched ? "checked" : ""} aria-label="Mark ${esc(x.title)} as watched">
      <span class="e">${x.emoji}</span>
      <div class="info"><div class="t">${esc(x.title)}</div>
        <div class="muted" style="font-size:13px">${x.kind === "series" ? "📺 Web Series" : "🎬 Movie"} · ${x.year} · ${esc(labels)}${stars(x)}</div></div>
      <button class="remove" aria-label="Remove">✕</button>`;
    $("input", li).onchange = (e) => {
      const l = loadWL();
      const it = l.find((y) => y.id === x.id);
      it.watched = e.target.checked;
      saveWL(l);
      if (it.watched) toast(`Finished "${x.title}" 🎉`);
      renderWatchlist();
    };
    $(".remove", li).onclick = () => { saveWL(loadWL().filter((y) => y.id !== x.id)); renderWatchlist(); };
    $(".t", li).onclick = () => openModal(x.id);
    ul.appendChild(li);
  });
  renderWLRecs(all);
}

async function renderWLRecs(all) {
  const box = $("#wl-recs");
  box.innerHTML = "";
  if (!all.length) return;
  const recs = await api("/api/recommend", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids: all.slice(0, 30).map((x) => x.id) }),
  });
  if (recs.length) box.appendChild(rowEl({ key: "wl-recs", emoji: "🍿", title: "You might also like", items: recs }));
}

function fillGenreFilter() {
  const sel = $("#wl-genre");
  Object.values(state.genres).forEach((g) => {
    const o = document.createElement("option");
    o.value = g.key; o.textContent = `${g.emoji} ${g.label}`;
    sel.appendChild(o);
  });
}

// ---------------- navigation 🧭 ----------------
function showView(v) {
  state.view = v;
  $("#view-browse").hidden = v !== "browse";
  $("#view-watchlist").hidden = v !== "watchlist";
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.view === v));
  if (v === "watchlist") renderWatchlist();
  else refreshForYou();
}

document.querySelectorAll(".nav-btn").forEach((b) => (b.onclick = () => showView(b.dataset.view)));
document.querySelectorAll(".kind").forEach((b) => (b.onclick = () => {
  state.kind = b.dataset.kind;
  document.querySelectorAll(".kind").forEach((x) => x.classList.toggle("active", x === b));
  loadBrowse();
}));
document.querySelectorAll(".wl-kind").forEach((b) => (b.onclick = () => {
  state.wlKind = b.dataset.wlkind;
  document.querySelectorAll(".wl-kind").forEach((x) => x.classList.toggle("active", x === b));
  renderWatchlist();
}));
$("#wl-genre").onchange = renderWatchlist;
$("#wl-hide-watched").onchange = renderWatchlist;
$("[data-home]").onclick = (e) => { e.preventDefault(); $("#search").value = ""; showView("browse"); setGenre(null); };

// ---------------- languages 🗣️ (TMDB mode lo matrame) ----------------
function renderLangs(langs) {
  const box = $("#lang-chips");
  if (!langs.length) { box.hidden = true; return; }
  box.hidden = false;
  box.innerHTML = "";
  [{ code: null, label: "🌐 All languages" }, ...langs].forEach((l) => {
    const b = document.createElement("button");
    b.className = "chip small" + (state.lang === l.code ? " active" : "");
    b.textContent = l.code ? l.label : l.label;
    b.onclick = () => { state.lang = l.code; renderLangs(langs); loadBrowse(); };
    box.appendChild(b);
  });
}

// ---------------- start 🚀 ----------------
(async function init() {
  saveWL(loadWL());
  const meta = await api("/api/meta");
  renderLangs(meta.languages);
  $("#attribution").innerHTML = meta.source === "tmdb"
    ? `<a href="https://www.themoviedb.org" target="_blank" rel="noopener"><img class="tmdb-logo" alt="TMDB" src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg" onerror="this.remove()"></a> ${esc(meta.attribution)}`
    : esc(meta.attribution);
  const genres = await api("/api/genres");
  genres.forEach((g) => (state.genres[g.key] = g));
  renderChips();
  fillGenreFilter();
  await loadBrowse();
})();
