/* FixMyHome statikus prototípus – fejléc, szerepkör- és témaváltó, kamu adatok, oldal-interakciók.
   Minden állapot localStorage-ben van, így a kattintások túlélik az oldalváltást. "Demóadatok visszaállítása" a jobb alsó DEMO panelben. */

const THEMES = { a: 'themes/a-hivis.css', b: 'themes/b-acel.css' };
const THEME_NAMES = { a: 'Építkezés', b: 'Acél' };
const LS = { theme: 'fmh-theme', role: 'fmh-role', db: 'fmh-db', jobs: 'fmh-munkak-szuro' };

// Téma beállítása még renderelés előtt (a script a <head>-ben fut), hogy ne villanjon.
const theme = THEMES[localStorage.getItem(LS.theme)] ? localStorage.getItem(LS.theme) : 'a';
document.getElementById('theme-css').href = THEMES[theme];
document.documentElement.dataset.theme = theme;

/* ---------- Ikonok (inline SVG) ---------- */
const ICONS = {
  logo: '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/><path d="m14.5 12.5-4.8 4.8a1.2 1.2 0 0 1-1.7-1.7l4.8-4.8a2.6 2.6 0 0 1 3.4-3.2l-1.6 1.6.5 1.2 1.2.5 1.6-1.6a2.6 2.6 0 0 1-3.4 3.2"/>',
  Villanyszerelő: '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z"/>',
  Vízszerelő: '<path d="M12 3s-6 6.6-6 11a6 6 0 0 0 12 0c0-4.4-6-11-6-11z"/><path d="M9.5 14.5a2.5 2.5 0 0 0 2.5 2.5"/>',
  Festő: '<rect x="3" y="3" width="14" height="6" rx="1.5"/><path d="M17 6h3v6h-8v2"/><rect x="10" y="14" width="4" height="7" rx="1"/>',
  Asztalos: '<path d="m14 7 3-3 3 3-3 3"/><path d="M17 10 7 20l-3-3L14 7"/><path d="m3 3 5 5"/>',
  Burkoló: '<rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/>',
  Lakatos: '<circle cx="8" cy="15" r="4.5"/><path d="m11.2 11.8 8.8-8.8"/><path d="m16.5 6.5 2.5 2.5"/><path d="m14 9 2 2"/>',
  all: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
  pin: '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
  locate: '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
  check: '<path d="M12 2 4 5v6c0 5 3.5 9.5 8 11 4.5-1.5 8-6 8-11V5z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
  map: '<path d="m9 4-6 2v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
  image: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
  inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  tool: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  ok: '<path d="m5 12 5 5L20 7"/>',
};
const icon = (n, cls = '') => `<svg class="icon ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[n] || ICONS.tool}</svg>`;

/* ---------- Kamu adatok ---------- */
const CATS = ['Villanyszerelő', 'Vízszerelő', 'Festő', 'Asztalos', 'Burkoló', 'Lakatos'];
const TOWNS = {
  Szabadka: { lat: 46.1003, lng: 19.6656, zip: '24000' }, Palics: { lat: 46.0989, lng: 19.7617, zip: '24413' },
  Topolya: { lat: 45.8156, lng: 19.6347, zip: '24300' }, Zenta: { lat: 45.9275, lng: 20.0897, zip: '24400' },
  Magyarkanizsa: { lat: 46.0667, lng: 20.0583, zip: '24420' }, Újvidék: { lat: 45.2671, lng: 19.8335, zip: '21000' },
};
const AV_COLORS = ['#1F6F5C', '#D9622B', '#1F2A44', '#7B3FA0', '#C62828', '#1565C0', '#8A5A00'];
const hoursAgo = h => Date.now() - h * 3600e3;

const DEFAULT_DB = () => ({
  mesterek: [
    { id: 1, name: 'Kovács Péter', trade: 'Villanyszerelő', town: 'Szabadka', lat: 46.1051, lng: 19.6602, price: '3000 din/órától', verified: true },
    { id: 2, name: 'Szabó Anikó', trade: 'Festő', town: 'Szabadka', lat: 46.0942, lng: 19.6721, price: '2500 din/órától', verified: true },
    { id: 3, name: 'Tóth Gábor', trade: 'Vízszerelő', town: 'Szabadka', lat: 46.1120, lng: 19.6488, price: '3500 din/órától', verified: false },
    { id: 4, name: 'Nagy Zoltán', trade: 'Asztalos', town: 'Szabadka', lat: 46.0880, lng: 19.6430, price: '4000 din/órától', verified: true },
    { id: 5, name: 'Horváth Ernő', trade: 'Burkoló', town: 'Szabadka', lat: 46.1185, lng: 19.6890, price: '3200 din/m²-től', verified: false },
    { id: 6, name: 'Varga Dénes', trade: 'Villanyszerelő', town: 'Palics', lat: 46.0995, lng: 19.7580, price: '2800 din/órától', verified: true },
    { id: 7, name: 'Molnár Ildikó', trade: 'Festő', town: 'Palics', lat: 46.1040, lng: 19.7660, price: '2600 din/órától', verified: false },
    { id: 8, name: 'Kiss Ferenc', trade: 'Vízszerelő', town: 'Szabadka', lat: 46.0790, lng: 19.6800, price: '3000 din/órától', verified: true },
    { id: 9, name: 'Lukács Róbert', trade: 'Lakatos', town: 'Topolya', lat: 45.8170, lng: 19.6380, price: '3500 din/órától', verified: true },
    { id: 10, name: 'Fekete Lajos', trade: 'Burkoló', town: 'Zenta', lat: 45.9290, lng: 20.0850, price: '3000 din/m²-től', verified: false },
  ],
  // A mester-nézet "saját" adatai
  me: { name: 'Kovács Péter', trades: ['Villanyszerelő', 'Vízszerelő'], town: 'Szabadka', available: true },
  ads: [
    { id: 101, title: 'Kiégett a konyhai biztosíték, nincs áram a konnektorokban', cat: 'Villanyszerelő', town: 'Szabadka', lat: 46.0985, lng: 19.6702, created: hoursAgo(2), status: 'open', client: 'Bálint Erika', desc: 'Tegnap este óta a konyhában egyik konnektor sem működik, a biztosíték mindig lecsap. Panellakás, 3. emelet.', images: 2 },
    { id: 102, title: 'Csillár felszerelése nappaliba', cat: 'Villanyszerelő', town: 'Palics', lat: 46.1010, lng: 19.7600, created: hoursAgo(26), status: 'open', client: 'Dudás Márk', desc: 'Megvan a lámpa, csak fel kellene szerelni. 2,8 m belmagasság.', images: 1 },
    { id: 103, title: 'Új konnektorok a gyerekszobába (3 db)', cat: 'Villanyszerelő', town: 'Szabadka', lat: 46.1130, lng: 19.6550, created: hoursAgo(5), status: 'open', client: 'Pásztor Júlia', desc: 'Falon kívüli kábelezés is jó, a lényeg, hogy biztonságos legyen.', images: 0 },
    { id: 104, title: 'Csöpög a fürdőszobai csap', cat: 'Vízszerelő', town: 'Szabadka', lat: 46.1000, lng: 19.6650, created: hoursAgo(1), status: 'open', client: 'Rácz Tamás', desc: 'Egykaros csaptelep, folyamatosan csöpög.', images: 1 },
    { id: 105, title: 'Villanyóra-szekrény cseréje', cat: 'Villanyszerelő', town: 'Szabadka', lat: 46.0920, lng: 19.6600, created: hoursAgo(72), status: 'closed', client: 'Vörös Ottó', desc: 'Régi, rozsdás mérőszekrény cseréje az EPS előírásai szerint.', images: 2 },
  ],
  applications: {}, // adId -> { msg, status }
  ownAd: {
    id: 1, title: 'Beázik a fürdőszoba mennyezete', cat: 'Vízszerelő', town: 'Szabadka', status: 'open', created: hoursAgo(20), images: [],
    desc: 'A felső szomszédnál valószínűleg egy cső szivárog, nálunk sárga folt van a mennyezeten és csöpög.',
    applicants: [
      { name: 'Tóth Gábor', trade: 'Vízszerelő', msg: 'Holnap délelőtt ki tudok menni felmérni, a felső lakásba is be kellene jutni.', status: 'pending' },
      { name: 'Kiss Ferenc', trade: 'Vízszerelő', msg: 'Jó napot! Hasonló beázást már sokat javítottam, csütörtöktől ráérek.', status: 'pending' },
      { name: 'Horváth Ernő', trade: 'Burkoló', msg: 'Ha a csempét is bontani kell, azt vállalom, vízszerelővel együtt dolgozom.', status: 'pending' },
    ],
  },
  jobs: [
    { client: 'Bálint Erika', place: 'Szabadka, Ősz utca 12.', work: 'Konyhai áramkör hibakeresése és biztosíték csere', status: 'in_progress' },
    { client: 'Szekeres Antal', place: 'Palics, Park utca 3.', work: 'Kültéri lámpák bekötése a teraszon', status: 'in_progress' },
    { client: 'Vörös Ottó', place: 'Szabadka, Zentai út 45.', work: 'Villanyóra-szekrény cseréje', status: 'closed' },
  ],
  services: [
    { id: 1, name: 'Háztartási villanyszerelés', trade: 'Villanyszerelő', desc: 'Konnektorok, kapcsolók, lámpák szerelése, hibakeresés.', price: '3000 din/órától', area: 'Szabadka és 10 km', status: 'published' },
    { id: 2, name: 'Biztosítéktábla csere', trade: 'Villanyszerelő', desc: 'Régi olvadóbiztosítékos tábla cseréje kismegszakítósra.', price: 'Megegyezés szerint', area: 'Szabadka, Palics', status: 'published' },
    { id: 3, name: 'Okosotthon-kapcsolók telepítése', trade: 'Villanyszerelő', desc: 'Wi-Fi-s kapcsolók és redőnyvezérlők beszerelése, beállítása.', price: '5000 din/órától', area: 'Szabadka', status: 'paused' },
  ],
});
let db;
try { db = JSON.parse(localStorage.getItem(LS.db)) || DEFAULT_DB(); } catch { db = DEFAULT_DB(); }
const save = () => {
  try { localStorage.setItem(LS.db, JSON.stringify(db)); }
  catch { db.ownAd.images = []; localStorage.setItem(LS.db, JSON.stringify(db)); toast('A képek túl nagyok a demó tárolóhoz – kép nélkül mentve.'); }
};

/* ---------- Segédek ---------- */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const params = new URLSearchParams(location.search);
const role = () => (localStorage.getItem(LS.role) === 'mester' ? 'mester' : 'user');
const initials = n => n.split(' ').map(w => w[0]).join('').slice(0, 2);
const avColor = n => AV_COLORS[[...n].reduce((a, c) => a + c.charCodeAt(0), 0) % AV_COLORS.length];
const avatar = (n, cls = '') => `<span class="avatar ${cls}" style="--av:${avColor(n)}" aria-hidden="true">${esc(initials(n))}</span>`;
function km(a, b) { // haversine
  const R = 6371, r = Math.PI / 180, dLat = (b.lat - a.lat) * r, dLng = (b.lng - a.lng) * r;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
const fmtKm = d => `${d.toFixed(1).replace('.', ',')} km`;
const pill = d => `<span class="pill-distance">${d.toFixed(1).replace('.', ',')}<small>km</small></span>`;
function ago(t) {
  const m = Math.round((Date.now() - t) / 60000);
  if (m < 60) return `${Math.max(m, 1)} perce`;
  if (m < 1440) return `${Math.round(m / 60)} órája`;
  return `${Math.round(m / 1440)} napja`;
}
const STATUS = {
  open: ['Nyitott', 'badge-open'], in_progress: ['Folyamatban', 'badge-progress'], closed: ['Lezárva', 'badge-closed'], withdrawn: ['Visszavonva', 'badge-withdrawn'],
  pending: ['Függőben', 'badge-pending'], accepted: ['Elfogadva', 'badge-accepted'], rejected: ['Elutasítva', 'badge-rejected'], app_withdrawn: ['Visszavonva', 'badge-withdrawn'],
  published: ['Közzétéve', 'badge-open'], paused: ['Szüneteltetve', 'badge-closed'],
};
const badge = s => `<span class="badge ${STATUS[s][1]}">${STATUS[s][0]}</span>`;
const stagger = el => $$(':scope > *', el).forEach((c, i) => c.style.setProperty('--i', i));
const ph = cat => `<div class="ph">${icon(cat)}</div>`;

function toast(msg) {
  let root = $('#toasts');
  if (!root) { root = document.createElement('div'); root.id = 'toasts'; root.setAttribute('aria-live', 'polite'); document.body.append(root); }
  const t = document.createElement('div');
  t.className = 'toast'; t.innerHTML = `${icon('ok')}<span>${esc(msg)}</span>`;
  root.append(t);
  setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 300); }, 3200);
}
// Átirányítás utáni toast
const flash = msg => sessionStorage.setItem('fmh-flash', msg);

function modal({ title, body = '', ok = 'Rendben', okClass = 'btn-primary', cancel = 'Mégse' }) {
  return new Promise(resolve => {
    const d = document.createElement('dialog');
    d.className = 'modal';
    d.innerHTML = `<form method="dialog"><div class="modal-body"><h2>${esc(title)}</h2>${body}</div>
      <div class="modal-actions"><button class="btn btn-secondary" value="cancel" formnovalidate>${cancel}</button><button class="btn ${okClass}" value="ok" data-ok>${ok}</button></div></form>`;
    document.body.append(d);
    d.addEventListener('close', () => { resolve(d.returnValue === 'ok' ? d : null); setTimeout(() => d.remove(), 0); });
    d.showModal();
  });
}

/* Űrlap-validáció: minden [required] mező mellé .field-error kerül. Igaz, ha minden rendben. */
function validate(form) {
  $$('.field-error', form).forEach(e => e.remove());
  $$('.form-field.has-error', form).forEach(f => f.classList.remove('has-error'));
  let first = null;
  $$('[required]', form).forEach(inp => {
    const field = inp.closest('.form-field');
    if (!field || field.hidden || field.closest('[hidden]')) return;
    const empty = inp.type === 'checkbox' || inp.type === 'radio'
      ? !$$(`[name="${inp.name}"]`, form).some(i => i.checked)
      : !inp.value.trim();
    if (!empty || field.classList.contains('has-error')) return;
    field.classList.add('has-error');
    field.insertAdjacentHTML('beforeend', `<p class="field-error" role="alert">${esc(inp.dataset.msg || 'Ezt a mezőt ki kell tölteni.')}</p>`);
    first ??= inp;
  });
  first?.focus();
  return !first;
}

/* ---------- Fejléc / menü ---------- */
// Szerepkörönként max. 3 menüpont + 1 kiemelt elem jobbra.
const MENU = {
  user: [['mesterek.html', 'Mesterek'], ['hirdetes-sajat.html', 'Hirdetéseim']],
  mester: [['hirdetesek.html', 'Hirdetések'], ['munkaim.html', 'Munkáim'], ['szolgaltatasaim.html', 'Szolgáltatásaim']],
};
const HOME = { user: 'mesterek.html', mester: 'hirdetesek.html' };
const page = location.pathname.split('/').pop() || 'login.html';
const ROLE_PAGES = {
  user: ['mesterek.html', 'hirdetes-sajat.html', 'hirdetes-uj.html'],
  mester: ['hirdetesek.html', 'hirdetes-reszlet.html', 'munkaim.html', 'szolgaltatasaim.html', 'szolgaltatas-uj.html', 'alapadatok.html'],
};
const PARENT = { 'hirdetes-reszlet.html': 'hirdetesek.html', 'szolgaltatas-uj.html': 'szolgaltatasaim.html' };

function renderHeader() {
  const r = role(), isAuth = document.body.dataset.auth !== undefined;
  const cur = PARENT[page] || page;
  const nav = isAuth ? '' : MENU[r].map(([h, t]) => `<a href="${h}"${h === cur ? ' aria-current="page"' : ''}>${t}</a>`).join('') + '<span class="nav-indicator" aria-hidden="true"></span>';
  const me = r === 'mester' ? db.me.name : 'Bálint Erika';
  const profile = `<details class="profile">
      <summary><span class="avatar" aria-hidden="true">${esc(initials(me))}</span><span class="profile-name"><b>${esc(me)}</b><small>${r === 'mester' ? 'Mester' : 'Felhasználó'}</small></span><span class="caret" aria-hidden="true">▾</span></summary>
      <div class="profile-menu">${r === 'mester' ? `<a href="alapadatok.html"${page === 'alapadatok.html' ? ' aria-current="page"' : ''}>${icon('user')}Alapadatok</a>` : ''}<a href="login.html">${icon('x')}Kilépés</a></div>
    </details>`;
  const cta = isAuth ? ''
    : (r === 'user' ? `<a class="btn btn-header" href="hirdetes-uj.html"${page === 'hirdetes-uj.html' ? ' aria-current="page"' : ''}>${icon('plus')}Hirdetés feladása</a>` : '') + profile;
  document.body.insertAdjacentHTML('afterbegin', `
  <header class="site-header"><div class="container">
    <a class="logo" href="${isAuth ? 'login.html' : HOME[r]}"><svg viewBox="0 0 24 24" class="icon" aria-hidden="true">${ICONS.logo}</svg><span>FixMy<b>Home</b></span></a>
    <nav class="main-nav" aria-label="Főmenü">${nav}</nav>
    <div class="header-cta">${cta}</div>
  </div></header>`);
  document.body.insertAdjacentHTML('beforeend', `
  <footer class="site-footer"><div class="container">© 2026 FixMyHome · Vajdaság</div></footer>
  <details class="demo-panel"><summary>DEMO</summary><div class="demo-body">
    <div class="row"><span>Szerep</span><div class="seg" role="group" aria-label="Szerepkör"><button data-role="user" aria-pressed="${r === 'user'}">Felhasználó</button><button data-role="mester" aria-pressed="${r === 'mester'}">Mester</button></div></div>
    <div class="row"><span>Téma</span><div class="seg" role="group" aria-label="Téma">${Object.keys(THEMES).map(k => `<button data-theme="${k}" aria-pressed="${k === theme}">${k.toUpperCase()} ${THEME_NAMES[k]}</button>`).join('')}</div></div>
    <button class="linklike" data-reset>Demóadatok visszaállítása</button>
  </div></details>`);

  // Csúszó aktív aláhúzás: a jelenlegi menüpont alatt áll, hoverre odacsúszik.
  const ind = $('.nav-indicator');
  if (ind) {
    const links = $$('.main-nav a'), home = links.find(a => a.hasAttribute('aria-current'));
    const move = a => { ind.style.opacity = a ? 1 : 0; if (a) { ind.style.width = `${a.offsetWidth}px`; ind.style.transform = `translateX(${a.offsetLeft}px)`; } };
    move(home);
    // Mobilon a menü vízszintesen görgethető: az aktív pont legyen látható.
    if (home) { const nav = home.parentElement; nav.scrollLeft = home.offsetLeft - (nav.clientWidth - home.offsetWidth) / 2; }
    links.forEach(a => a.addEventListener('mouseenter', () => move(a)));
    $('.main-nav').addEventListener('mouseleave', () => move(home));
    document.fonts?.ready.then(() => move(home));
  }

  // Profil-lenyíló: kattintás máshova vagy Esc bezárja.
  const prof = $('.profile');
  if (prof) {
    document.addEventListener('click', e => { if (!prof.contains(e.target)) prof.open = false; });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') prof.open = false; });
  }

  $$('.seg [data-role]').forEach(b => b.onclick = () => {
    localStorage.setItem(LS.role, b.dataset.role);
    if (isAuth) return location.reload();
    const ok = ROLE_PAGES[b.dataset.role].includes(page);
    location.href = ok ? location.href : HOME[b.dataset.role];
  });
  $$('.seg [data-theme]').forEach(b => b.onclick = () => { localStorage.setItem(LS.theme, b.dataset.theme); location.reload(); });
  $('[data-reset]').onclick = () => { localStorage.removeItem(LS.db); localStorage.removeItem(LS.jobs); location.reload(); };
}

/* ---------- Kártyák ---------- */
const trade = t => `<span class="chip chip-trade">${icon(t)}${esc(t)}</span>`;
// Szakma-színkód: a Django slugify-jával azonos slug (ékezet nélkül, kisbetű).
const slug = t => t.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-');
const cat = t => `cat-${slug(t)}`;
const tIcon = t => `<span class="trade-icon" aria-hidden="true">${icon(t)}</span>`;
const tLabel = t => `<span class="trade-label">${esc(t)}</span>`;
const DESC = { Villanyszerelő: 'Lakossági villanyszerelés, hibaelhárítás', Vízszerelő: 'Csőtörés, csaptelep, fürdőszoba-szerelés', Festő: 'Szobafestés, mázolás, tapétázás', Asztalos: 'Bútorjavítás, beépített szekrény, ajtók', Burkoló: 'Csempézés, járólap, fürdőszoba-felújítás', Lakatos: 'Zárcsere, kapu, korlát, fémszerkezet' };
function mesterCard(m, d, tag = 'li') {
  const avail = m.available ?? m.id % 3 !== 0;
  return `<${tag} class="card hoverable ${cat(m.trade)}" data-id="${m.id}">
    <div class="card-main">${tIcon(m.trade)}<div>
      <div class="card-top"><div><h3>${esc(m.name)}</h3>${tLabel(m.trade)}</div>${pill(d)}</div>
      <p class="card-desc">${esc(m.desc || DESC[m.trade])}</p>
      <div class="card-facts"><span>${icon('pin')}${esc(m.town)}</span><span class="price">${esc(m.price)}</span><span class="${avail ? 'avail' : 'avail avail-off'}">${avail ? 'Most elérhető' : 'Most nem elérhető'}</span></div>
      <p class="rating-none">Még nincs értékelés</p>
    </div></div>
    <div class="card-actions"><a class="btn btn-secondary btn-sm" href="hirdetes-uj.html?kat=${encodeURIComponent(m.trade)}">Ajánlatot kérek</a></div>
  </${tag}>`;
}
const empty = (ic, title, text, action = '') => `<div class="empty-state">${icon(ic)}<h3>${title}</h3><p>${text}</p>${action}</div>`;
const head = (title, lead, action = '', eyebrow = '') => `<div class="page-head"><div>${eyebrow ? `<p class="eyebrow">${eyebrow}</p>` : ''}<h1 class="page-title">${esc(title)}</h1><p class="page-lead">${lead}</p></div>${action}</div>`;

/* ---------- Oldalak ---------- */
const PAGES = {
  login() {
    $('#login-form').onsubmit = e => {
      e.preventDefault();
      const f = e.target;
      $('.form-alert', f)?.remove();
      if (!validate(f)) return;
      if (f.password.value !== 'demo') {
        f.insertAdjacentHTML('afterbegin', '<p class="form-alert" role="alert">Hibás e-mail-cím vagy jelszó. Próbáld újra!</p>');
        f.password.value = ''; f.password.focus(); return;
      }
      flash('Sikeres belépés. Üdv újra!');
      location.href = HOME[role()];
    };
  },

  register() {
    const f = $('#register-form');
    const sync = () => { $('#trade-field').hidden = f.role.value !== 'mester'; };
    $$('[name=role]', f).forEach(r => r.onchange = sync);
    f.role.value = role(); sync();
    f.onsubmit = e => {
      e.preventDefault();
      if (!validate(f)) return;
      localStorage.setItem(LS.role, f.role.value);
      flash(`Sikeres regisztráció – üdv a FixMyHome-on, ${f.name.value.split(' ')[0]}!`);
      location.href = HOME[f.role.value];
    };
  },

  mesterek() {
    let center = { ...TOWNS.Szabadka, label: 'Szabadka' }, radius = 5, cat = null, view = 'list', map, layer, meMarker;
    const tabs = $('#cat-tabs');
    tabs.innerHTML = [['all', 'Mind'], ...CATS.map(c => [c, c])].map(([k, t]) => `<button data-cat="${k}" aria-pressed="${k === 'all'}">${t}</button>`).join('');
    tabs.onclick = e => {
      const b = e.target.closest('[data-cat]'); if (!b) return;
      cat = b.dataset.cat === 'all' ? null : b.dataset.cat;
      $$('[data-cat]', tabs).forEach(x => x.setAttribute('aria-pressed', x === b)); render();
    };
    const setRadius = r => { radius = r; $$('[data-radius]').forEach(x => x.setAttribute('aria-pressed', +x.dataset.radius === r)); render(); };
    $$('[data-radius]').forEach(b => b.onclick = () => setRadius(+b.dataset.radius));
    $$('[data-view]').forEach(b => b.onclick = () => {
      view = b.dataset.view;
      $$('[data-view]').forEach(x => x.setAttribute('aria-pressed', x === b));
      $$('[data-view-panel]').forEach(p => { p.hidden = p.dataset.viewPanel !== view; });
      if (view === 'map') initMap(); render();
    });
    const setCenter = (c, msg) => { center = c; $('#where-input').value = c.label; toast(msg); render(); };
    $('#locate-btn').onclick = () => {
      if (!navigator.geolocation) return toast('A böngésző nem támogatja a helymeghatározást – írd be a települést.');
      navigator.geolocation.getCurrentPosition(
        p => setCenter({ lat: p.coords.latitude, lng: p.coords.longitude, label: 'Jelenlegi helyed' }, 'Megvan a helyed!'),
        () => { toast('Nem kaptunk helyengedélyt – írd be a települést vagy irányítószámot.'); $('#where-input').focus(); },
        { timeout: 8000 });
    };
    $('#where-form').onsubmit = e => {
      e.preventDefault();
      const q = $('#where-input').value.trim().toLowerCase();
      const hit = Object.entries(TOWNS).find(([n, t]) => n.toLowerCase().startsWith(q) || t.zip === q);
      if (!q || !hit) return toast('Nem találtuk – próbáld: Szabadka, Zenta, Topolya, 24000…');
      setCenter({ ...hit[1], label: hit[0] }, `Keresés innen: ${hit[0]}`);
    };

    function initMap() {
      if (map || !window.L) return;
      map = L.map('map').setView([center.lat, center.lng], 12);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '&copy; OpenStreetMap' }).addTo(map);
      layer = L.layerGroup().addTo(map);
      map.on('click', () => $('#sheet').classList.remove('open'));
    }
    function drawMap(list) {
      if (!map) return;
      setTimeout(() => map.invalidateSize(), 0);
      layer.clearLayers(); meMarker?.remove();
      meMarker = L.marker([center.lat, center.lng], { icon: L.divIcon({ className: '', html: '<div class="map-me"></div>', iconSize: [18, 18] }), title: 'Itt vagy' }).addTo(map);
      L.circle([center.lat, center.lng], { radius: radius * 1000, color: getComputedStyle(document.body).getPropertyValue('--ink').trim(), weight: 2, fillOpacity: .05 }).addTo(layer);
      list.forEach(({ m, d }) => {
        const mk = L.marker([m.lat, m.lng], { title: m.name, icon: L.divIcon({ className: '', html: `<div class="map-pin"><span>${initials(m.name)}</span></div>`, iconSize: [36, 36], iconAnchor: [18, 18] }) }).addTo(layer);
        mk.on('click', ev => {
          L.DomEvent.stopPropagation(ev);
          $$('.map-pin.active').forEach(p => p.classList.remove('active'));
          mk.getElement().firstChild.classList.add('active');
          $('#sheet-body').innerHTML = mesterCard(m, d, 'div');
          $('#sheet').classList.add('open');
        });
      });
      map.fitBounds(L.latLng(center.lat, center.lng).toBounds(radius * 2200));
    }
    $('#sheet-close').onclick = () => $('#sheet').classList.remove('open');

    function render() {
      const list = db.mesterek.map(m => ({ m, d: km(center, m) }))
        .filter(x => x.d <= radius && (!cat || x.m.trade === cat)).sort((a, b) => a.d - b.d);
      $('#result-count').textContent = `${list.length} mester ${radius} km-en belül, ${center.label} körül${cat ? ` · ${cat}` : ''}`;
      const el = $('#mester-list');
      el.innerHTML = list.length ? list.map(x => mesterCard(x.m, x.d)).join('')
        : empty('search', 'Nincs mester ebben a körzetben', radius < 20 ? 'Pár kilométerrel arrébb lehet, hogy van megfelelő szakember.' : 'Adj fel hirdetést, és szólunk a környékbeli mestereknek.',
          radius < 20 ? '<button class="btn btn-secondary" data-try20>Próbáld 20 km-rel</button>' : '<a class="btn btn-secondary" href="hirdetes-uj.html">Hirdetés feladása</a>');
      stagger(el);
      $('[data-try20]', el)?.addEventListener('click', () => setRadius(20));
      $('#sheet').classList.remove('open');
      if (view === 'map') drawMap(list);
    }
    render();
  },

  'hirdetes-uj'() {
    const f = $('#ad-form'), thumbs = $('#thumbs'), files = [];
    f.cat.innerHTML = '<option value="">Válassz…</option>' + CATS.map(c => `<option>${c}</option>`).join('');
    f.town.innerHTML = '<option value="">Válassz…</option>' + Object.keys(TOWNS).map(c => `<option>${c}</option>`).join('');
    if (params.get('kat')) f.cat.value = params.get('kat');
    const drop = $('#dropzone');
    const add = list => [...list].filter(x => x.type.startsWith('image/')).forEach(file => {
      const r = new FileReader();
      r.onload = () => { files.push(r.result); draw(); };
      r.readAsDataURL(file);
    });
    const draw = () => {
      thumbs.innerHTML = files.map((src, i) => `<figure><img src="${src}" alt="Feltöltött kép ${i + 1}"><button type="button" data-del="${i}" aria-label="Kép törlése">×</button></figure>`).join('');
    };
    thumbs.onclick = e => { const b = e.target.closest('[data-del]'); if (b) { files.splice(+b.dataset.del, 1); draw(); } };
    f.images.onchange = () => { add(f.images.files); f.images.value = ''; };
    drop.onclick = () => f.images.click();
    drop.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); f.images.click(); } };
    drop.ondragover = e => { e.preventDefault(); drop.classList.add('drag'); };
    drop.ondragleave = () => drop.classList.remove('drag');
    drop.ondrop = e => { e.preventDefault(); drop.classList.remove('drag'); add(e.dataTransfer.files); };

    f.onsubmit = async e => {
      e.preventDefault();
      if (!validate(f)) return;
      const btn = $('[type=submit]', f); btn.disabled = true; btn.textContent = 'Mentés…';
      db.ownAd = { id: Date.now(), title: f.title.value.trim(), desc: f.desc.value.trim(), cat: f.cat.value, town: f.town.value, status: 'open', created: Date.now(),
        images: await Promise.all(files.map(shrink)), applicants: DEFAULT_DB().ownAd.applicants.map(a => ({ ...a, trade: a.trade === 'Burkoló' ? a.trade : f.cat.value })) };
      save();
      flash('Hirdetés feladva! A környékbeli mesterek értesítést kapnak.');
      location.href = 'hirdetes-sajat.html';
    };
  },

  'hirdetes-sajat'() {
    const root = $('#own-ad');
    const draw = () => {
      const a = db.ownAd, s = a.status;
      const idx = ['open', 'in_progress', 'closed'].indexOf(s);
      const imgs = a.images.length ? a.images.map((src, i) => `<div><img src="${src}" alt="Kép ${i + 1}"></div>`).join('') : ph(a.cat) + ph(a.cat);
      const lead = { open: 'Válaszd ki a jelentkezők közül, akivel dolgozni szeretnél.', in_progress: 'Kiválasztottad a mestert. Ha elkészült a munka, zárd le a hirdetést.', closed: 'A munka lezárva. Köszönjük, hogy a FixMyHome-ot választottad!', withdrawn: 'A hirdetést visszavontad, a mesterek már nem látják.' }[s];
      const action = s === 'in_progress' ? '<button class="btn btn-primary" data-close>Lezárás</button>'
        : s === 'open' ? '<button class="btn btn-secondary" data-withdraw>Visszavonás</button>' : '';
      root.innerHTML = head(a.title, lead, action, 'Hirdetéseim') + `
        <div class="card ${cat(a.cat)}">
          <div class="card-main">${tIcon(a.cat)}<div>
            <div class="card-top"><div>${tLabel(a.cat)}<p class="card-sub" style="margin-top:8px">${icon('pin')}${esc(a.town)} · ${ago(a.created)}</p></div>${badge(s)}</div>
          </div></div>
          <p>${esc(a.desc)}</p>
          <div class="gallery">${imgs}</div>
          <ol class="stepper ${s === 'withdrawn' ? 'is-withdrawn' : ''}" aria-label="Hirdetés állapota">
            ${['Nyitott', 'Folyamatban', 'Lezárva'].map((t, i) => `<li class="${s === 'withdrawn' ? '' : i < idx || s === 'closed' ? 'done' : i === idx ? 'current' : ''}">${t}</li>`).join('')}
          </ol>
        </div>
        <h2 class="section-title">Jelentkezők (${a.applicants.length})</h2>
        ${a.applicants.length ? `<ul class="card-list" id="applicants">${a.applicants.map((p, i) => `
          <li class="card ${cat(p.trade)}">
            <div class="card-main">${tIcon(p.trade)}<div>
              <div class="card-top"><div><h3>${esc(p.name)}</h3>${tLabel(p.trade)}</div>${badge(p.status)}</div>
              <p>„${esc(p.msg)}”</p>
              <p class="rating-none">Még nincs értékelés</p>
            </div></div>
            ${s === 'open' && p.status === 'pending' ? `<div class="card-actions"><button class="btn btn-secondary" data-pick="${i}">Kiválasztom</button></div>` : ''}
          </li>`).join('')}</ul>` : empty('inbox', 'Még nincs jelentkező', 'Amint egy környékbeli mester jelentkezik, itt látod.')}`;
      $$('#applicants').forEach(stagger);
    };
    root.onclick = async e => {
      const a = db.ownAd;
      const pick = e.target.closest('[data-pick]');
      if (pick) {
        const p = a.applicants[+pick.dataset.pick];
        if (!await modal({ title: `${p.name} kiválasztása`, body: '<p>A többi jelentkezést elutasítjuk, a hirdetés Folyamatban állapotba kerül.</p>', ok: 'Kiválasztom' })) return;
        a.applicants.forEach(x => { x.status = x === p ? 'accepted' : 'rejected'; });
        a.status = 'in_progress'; save(); draw(); toast(`${p.name} kiválasztva – értesítettük.`);
      }
      if (e.target.closest('[data-withdraw]')) {
        if (!await modal({ title: 'Biztosan visszavonod?', body: '<p>A mesterek többé nem látják a hirdetést.</p>', ok: 'Visszavonás', okClass: 'btn-danger' })) return;
        a.status = 'withdrawn'; a.applicants.forEach(x => { if (x.status === 'pending') x.status = 'rejected'; }); save(); draw(); toast('Hirdetés visszavonva.');
      }
      if (e.target.closest('[data-close]')) {
        if (!await modal({ title: 'Lezárod a munkát?', body: '<p>Akkor zárd le, ha a mester elvégezte a munkát.</p>', ok: 'Lezárás' })) return;
        a.status = 'closed'; save(); draw(); toast('Munka lezárva. Köszönjük!');
      }
    };
    draw();
  },

  hirdetesek() {
    const me = db.me, from = TOWNS[me.town];
    $('#my-trades').textContent = `${me.trades.join(', ')} munkák ${me.town} 20 km-es körzetében, a legközelebbi elöl.`;
    const list = db.ads.filter(a => a.status === 'open' && me.trades.includes(a.cat)).map(a => ({ a, d: km(from, a) })).filter(x => x.d <= 20).sort((x, y) => x.d - y.d);
    const el = $('#ad-list');
    el.innerHTML = list.length ? list.map(({ a, d }) => `
      <li class="card hoverable ${cat(a.cat)}">
        <div class="card-main">${tIcon(a.cat)}<div>
          <div class="card-top"><div><h3>${esc(a.title)}</h3>${tLabel(a.cat)}</div>${pill(d)}</div>
          <p class="card-desc">${esc(a.desc)}</p>
          <div class="card-facts">${db.applications[a.id]?.status === 'pending' ? '<span class="badge badge-pending">Jelentkeztél</span>' : badge(a.status)}<span>${icon('pin')}${esc(a.town)}</span><span>${icon('clock')}${ago(a.created)}</span></div>
        </div></div>
        <div class="card-actions"><a class="btn btn-secondary btn-sm" href="hirdetes-reszlet.html?id=${a.id}">Megnézem</a></div>
      </li>`).join('')
      : empty('inbox', 'Nincs nyitott hirdetés a környéken', 'Most senki nem keres a szakmádban 20 km-en belül. Bővítsd a szakmáidat az alapadatoknál!', '<a class="btn btn-secondary" href="alapadatok.html">Alapadatok</a>');
    stagger(el);
  },

  'hirdetes-reszlet'() {
    const a = db.ads.find(x => x.id === +params.get('id')) || db.ads[0];
    const root = $('#ad-detail');
    const draw = () => {
      const app = db.applications[a.id], closed = a.status !== 'open', applied = app?.status === 'pending';
      const action = closed ? '<button class="btn btn-primary" disabled>Jelentkezem</button>'
        : applied ? '<button class="btn btn-secondary" data-unapply>Jelentkezés visszavonása</button>'
        : '<button class="btn btn-primary" data-apply>Jelentkezem</button>';
      const lead = closed ? `Ez a hirdetés már ${STATUS[a.status][0].toLowerCase()}, nem lehet jelentkezni.`
        : applied ? 'Jelentkeztél. Ha a hirdető kiválaszt, megjelenik a Munkáim között.'
        : 'Ha vállalod, jelentkezz egy rövid üzenettel a hirdetőnek.';
      root.innerHTML = `<a href="hirdetesek.html" class="btn btn-ghost">← Hirdetések</a>` + head(a.title, lead, action, a.cat) + `
        <div class="card ${cat(a.cat)}">
          <div class="card-top"><div>${applied ? '<span class="badge badge-pending">Jelentkeztél</span>' : badge(a.status)}
            <p class="card-sub" style="margin-top:12px">${icon('user')}${esc(a.client)} · ${icon('pin')}${esc(a.town)} · ${ago(a.created)}</p></div>${pill(km(TOWNS[db.me.town], a))}</div>
          <p>${esc(a.desc)}</p>
          ${applied ? `<p class="demo-hint">Az üzeneted: „${esc(app.msg)}”</p>` : ''}
          ${a.images ? `<div class="gallery">${Array.from({ length: a.images }, () => ph(a.cat)).join('')}</div>` : ''}
        </div>`;
    };
    root.onclick = async e => {
      if (e.target.closest('[data-apply]')) {
        const d = await modal({ title: 'Jelentkezés a munkára', ok: 'Jelentkezem', body: `<div class="form-field"><label for="apply-msg">Rövid üzenet a hirdetőnek</label><textarea id="apply-msg" maxlength="300" placeholder="Pl. Holnap délután ki tudok menni felmérni."></textarea></div>` });
        if (!d) return;
        db.applications[a.id] = { msg: $('#apply-msg', d).value.trim() || 'Szívesen elvállalom.', status: 'pending' };
        save(); draw(); toast('Jelentkezés elküldve!');
      }
      if (e.target.closest('[data-unapply]')) {
        if (!await modal({ title: 'Visszavonod a jelentkezést?', ok: 'Visszavonás', okClass: 'btn-danger' })) return;
        db.applications[a.id].status = 'app_withdrawn'; save(); draw(); toast('Jelentkezés visszavonva.');
      }
    };
    draw();
  },

  munkaim() {
    const FILTERS = { in_progress: 'Folyamatban', closed: 'Lezárva', mind: 'Mind' };
    let f = params.get('allapot') || localStorage.getItem(LS.jobs) || 'in_progress';
    if (!FILTERS[f]) f = 'in_progress';
    const bar = $('#job-filter');
    bar.innerHTML = Object.entries(FILTERS).map(([k, t]) => `<button data-f="${k}" aria-pressed="${k === f}">${t}</button>`).join('');
    bar.onclick = e => {
      const b = e.target.closest('[data-f]'); if (!b) return;
      f = b.dataset.f; localStorage.setItem(LS.jobs, f);
      history.replaceState(null, '', `?allapot=${f}`);
      $$('[data-f]', bar).forEach(x => x.setAttribute('aria-pressed', x === b)); draw();
    };
    const draw = () => {
      const list = db.jobs.filter(j => f === 'mind' || j.status === f), el = $('#job-list');
      el.innerHTML = list.length ? list.map(j => `
        <li class="card hoverable ${cat(j.trade || db.me.trades[0])}">
          <div class="card-main">${tIcon(j.trade || db.me.trades[0])}<div>
            <div class="card-top"><div><h3>${esc(j.work)}</h3>${tLabel(j.trade || db.me.trades[0])}</div>${badge(j.status)}</div>
            <div class="card-facts"><span>${icon('user')}${esc(j.client)}</span><span>${icon('pin')}${esc(j.place)}</span><span class="muted">${icon('calendar')}Még nincs időpont</span></div>
          </div></div>
        </li>`).join('')
        : empty('inbox', 'Nincs ilyen munkád', f === 'closed' ? 'Még egy munkát sem zártál le.' : 'Jelentkezz a környékbeli hirdetésekre, és itt látod az elvállalt munkákat.', '<a class="btn btn-secondary" href="hirdetesek.html">Hirdetések</a>');
      stagger(el);
    };
    draw();
  },

  szolgaltatasaim() {
    const el = $('#service-list');
    const draw = () => {
      el.innerHTML = db.services.length ? db.services.map(s => `
        <li class="card hoverable ${cat(s.trade)}" data-id="${s.id}">
          <div class="card-main">${tIcon(s.trade)}<div>
            <div class="card-top"><div><h3>${esc(s.name)}</h3>${tLabel(s.trade)}</div>${badge(s.status)}</div>
            <p class="card-desc">${esc(s.desc)}</p>
            <div class="card-facts"><span class="price">${esc(s.price)}</span><span>${icon('pin')}${esc(s.area)}</span></div>
          </div></div>
          <div class="card-actions">
            <a class="btn btn-secondary btn-sm" href="szolgaltatas-uj.html?id=${s.id}">Szerkesztés</a>
            <button class="btn btn-secondary btn-sm" data-toggle>${s.status === 'published' ? 'Szüneteltetés' : 'Közzététel'}</button>
            <button class="btn btn-ghost btn-sm" data-del>Törlés</button>
          </div>
        </li>`).join('')
        : empty('tool', 'Még nincs szolgáltatásod', 'Hirdesd meg, mit vállalsz – így az ügyfelek könnyebben megtalálnak.');
      stagger(el);
    };
    el.onclick = async e => {
      const card = e.target.closest('[data-id]'); if (!card) return;
      const s = db.services.find(x => x.id === +card.dataset.id);
      if (e.target.closest('[data-toggle]')) {
        s.status = s.status === 'published' ? 'paused' : 'published'; save(); draw();
        toast(s.status === 'paused' ? 'Szolgáltatás szüneteltetve.' : 'Szolgáltatás újra közzétéve.');
      }
      if (e.target.closest('[data-del]')) {
        if (!await modal({ title: 'Biztosan törlöd?', body: `<p>A(z) <b>${esc(s.name)}</b> szolgáltatás végleg törlődik.</p>`, ok: 'Törlés', okClass: 'btn-danger' })) return;
        db.services = db.services.filter(x => x !== s); save(); draw(); toast('Szolgáltatás törölve.');
      }
    };
    draw();
  },

  'szolgaltatas-uj'() {
    const f = $('#service-form');
    f.trade.innerHTML = '<option value="">Válassz…</option>' + CATS.map(c => `<option>${c}</option>`).join('');
    const edit = db.services.find(x => x.id === +params.get('id'));
    if (edit) {
      $('.page-title').textContent = 'Szolgáltatás szerkesztése';
      ['name', 'trade', 'desc', 'price', 'area'].forEach(k => { f[k].value = edit[k]; });
      $('[type=submit]', f).textContent = 'Mentés';
    }
    f.onsubmit = e => {
      e.preventDefault();
      if (!validate(f)) return;
      const data = Object.fromEntries(['name', 'trade', 'desc', 'price', 'area'].map(k => [k, f[k].value.trim()]));
      if (edit) Object.assign(edit, data);
      else db.services.unshift({ id: Date.now(), status: 'published', ...data });
      save(); flash(edit ? 'Változások mentve.' : 'Szolgáltatás közzétéve!');
      location.href = 'szolgaltatasaim.html';
    };
  },

  alapadatok() {
    const f = $('#profile-form');
    $('#trade-chips').innerHTML = CATS.map(c => `<label class="chip"><input type="checkbox" name="trades" value="${c}" ${db.me.trades.includes(c) ? 'checked' : ''} required data-msg="Legalább egy szakmát válassz.">${c}</label>`).join('');
    f.town.innerHTML = Object.keys(TOWNS).map(c => `<option ${c === db.me.town ? 'selected' : ''}>${c}</option>`).join('');
    f.available.checked = db.me.available;
    const lbl = () => { $('#avail-text').textContent = f.available.checked ? 'Az ügyfelek most elérhetőként látnak.' : 'Most nem jelensz meg az elérhető mesterek között.'; };
    f.available.onchange = () => { lbl(); db.me.available = f.available.checked; save(); toast(f.available.checked ? 'Most elérhető vagy.' : 'Elérhetőség kikapcsolva.'); };
    lbl();
    f.onsubmit = e => {
      e.preventDefault();
      if (!validate(f)) return;
      db.me.trades = $$('[name=trades]:checked', f).map(i => i.value); db.me.town = f.town.value; save();
      toast('Alapadatok mentve.');
    };
  },
};

// Kép kicsinyítése, hogy beférjen a localStorage-be.
function shrink(src) {
  return new Promise(res => {
    const img = new Image();
    img.onload = () => {
      const s = Math.min(1, 480 / Math.max(img.width, img.height)), c = document.createElement('canvas');
      c.width = img.width * s; c.height = img.height * s;
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      res(c.toDataURL('image/jpeg', .7));
    };
    img.onerror = () => res(src);
    img.src = src;
  });
}

document.addEventListener('DOMContentLoaded', () => {
  renderHeader();
  PAGES[document.body.dataset.page]?.();
  const msg = sessionStorage.getItem('fmh-flash');
  if (msg) { sessionStorage.removeItem('fmh-flash'); setTimeout(() => toast(msg), 250); }
});
