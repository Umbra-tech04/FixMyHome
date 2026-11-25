/* FixMyHome V2 – oldalsáv, szerepváltó, kamu adatok, toast/megerősítés és a 3 felhasználói oldal logikája.
   A design/app.js-től független. Állapot: localStorage „fmh2-role”, „fmh2-ad”. */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const slug = t => t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const page = document.body.dataset.page || '';
  const params = new URLSearchParams(location.search);

  const ICONS = {
    logo: '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/><path d="m14.5 12.5-4.8 4.8a1.2 1.2 0 0 1-1.7-1.7l4.8-4.8a2.6 2.6 0 0 1 3.4-3.2l-1.6 1.6.5 1.2 1.2.5 1.6-1.6a2.6 2.6 0 0 1-3.4 3.2"/>',
    Villanyszerelő: '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z"/>',
    Vízszerelő: '<path d="M12 3s-6 6.6-6 11a6 6 0 0 0 12 0c0-4.4-6-11-6-11z"/>',
    Festő: '<rect x="3" y="3" width="14" height="6"/><path d="M17 6h3v6h-8v2"/><rect x="10" y="14" width="4" height="7"/>',
    Asztalos: '<path d="m14 7 3-3 3 3-3 3"/><path d="M17 10 7 20l-3-3L14 7"/><path d="m3 3 5 5"/>',
    Burkoló: '<rect x="3" y="3" width="8" height="8"/><rect x="13" y="3" width="8" height="8"/><rect x="3" y="13" width="8" height="8"/><rect x="13" y="13" width="8" height="8"/>',
    Lakatos: '<circle cx="8" cy="15" r="4.5"/><path d="m11.2 11.8 8.8-8.8"/><path d="m16.5 6.5 2.5 2.5"/><path d="m14 9 2 2"/>',
    image: '<rect x="3" y="3" width="18" height="18"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/>',
  };
  const icon = n => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${ICONS[n] || ''}</svg>`;
  const CATS = ['Villanyszerelő', 'Vízszerelő', 'Festő', 'Asztalos', 'Burkoló', 'Lakatos'];
  // Magyar név → [lat, lng, szerb név]; a keresés mindkét névre talál (ékezet nélkül is).
  const TOWNS = {
    Szabadka: [46.1003, 19.6656, 'Subotica'], Palics: [46.0989, 19.7617, 'Palić'], Zenta: [45.9275, 20.0897, 'Senta'],
    Óbecse: [45.6167, 20.0333, 'Bečej'], Topolya: [45.8156, 19.6347, 'Bačka Topola'], Magyarkanizsa: [46.0667, 20.0583, 'Kanjiža'],
    Ada: [45.8022, 20.1289, 'Ada'], Mohol: [45.7656, 20.1306, 'Mol'], Csantavér: [45.9130, 19.7650, 'Čantavir'],
    Kishegyes: [45.7083, 19.6681, 'Mali Iđoš'], Horgos: [46.1567, 19.9744, 'Horgoš'], Törökkanizsa: [46.0500, 20.1000, 'Novi Kneževac'],
    Szenttamás: [45.5486, 19.7928, 'Srbobran'], Temerin: [45.4083, 19.8889, 'Temerin'], Zombor: [45.7742, 19.1122, 'Sombor'],
    Újvidék: [45.2671, 19.8335, 'Novi Sad'],
  };
  const norm = t => slug(t).replace(/[^a-z0-9 ]/g, '');
  const findTowns = q => { q = norm(q.trim()); return Object.entries(TOWNS).filter(([hu, v]) => !q || norm(hu).startsWith(q) || norm(v[2]).startsWith(q) || norm(hu).includes(q) || norm(v[2]).includes(q)); };
  const MESTEREK = [
    ['Kovács Péter', 'Villanyszerelő', 46.1051, 19.6602, 'Szabadka', '3000 din/óra'], ['Szabó Anikó', 'Festő', 46.0942, 19.6721, 'Szabadka', '2500 din/óra'],
    ['Tóth Gábor', 'Vízszerelő', 46.1120, 19.6488, 'Szabadka', '3500 din/óra'], ['Nagy Zoltán', 'Asztalos', 46.0880, 19.6430, 'Szabadka', '4000 din/óra'],
    ['Horváth Ernő', 'Burkoló', 46.1185, 19.6890, 'Szabadka', '3200 din/m²'], ['Varga Dénes', 'Villanyszerelő', 46.0995, 19.7580, 'Palics', '2800 din/óra'],
    ['Molnár Ildikó', 'Festő', 46.1040, 19.7660, 'Palics', '2600 din/óra'], ['Kiss Ferenc', 'Vízszerelő', 46.0790, 19.6800, 'Szabadka', '3000 din/óra'],
    ['Lukács Róbert', 'Lakatos', 45.8170, 19.6380, 'Topolya', '3500 din/óra'], ['Fekete Lajos', 'Burkoló', 45.9290, 20.0850, 'Zenta', '3000 din/m²'],
    ['Bodor Gyula', 'Lakatos', 46.1090, 19.6720, 'Szabadka', '3300 din/óra'], ['Papp Edit', 'Asztalos', 46.0720, 19.6560, 'Szabadka', '3800 din/óra'],
    ['Sárközi Attila', 'Villanyszerelő', 45.9310, 20.0940, 'Zenta', '2900 din/óra'], ['Kovács Anna', 'Festő', 45.9250, 20.0810, 'Zenta', '2500 din/óra'],
    ['Takács Imre', 'Vízszerelő', 45.6190, 20.0400, 'Óbecse', '3200 din/óra'], ['Pintér Zsolt', 'Asztalos', 45.6120, 20.0280, 'Óbecse', '3700 din/óra'],
    ['Rácz Mónika', 'Burkoló', 45.6220, 20.0450, 'Óbecse', '3100 din/m²'],
  ].map(([name, trade, lat, lng, town, price], id) => ({ id, name, trade, lat, lng, town, price }));
  const km = (a, b) => { const R = 6371, r = Math.PI / 180, dLat = (b[0] - a[0]) * r, dLng = (b[1] - a[1]) * r; const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dLng / 2) ** 2; return 2 * R * Math.asin(Math.sqrt(h)); };
  const fmt = d => d.toFixed(1).replace('.', ',');
  const initials = n => n.split(' ').map(w => w[0]).join('').slice(0, 2);

  /* ---------- Toast + megerősítés ---------- */
  function toast(msg) {
    let root = $('#toasts');
    if (!root) { root = document.createElement('div'); root.id = 'toasts'; root.setAttribute('aria-live', 'polite'); document.body.append(root); }
    const t = document.createElement('div'); t.className = 'toast'; t.textContent = msg; root.append(t);
    setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 300); }, 3200);
  }
  function confirmBox(title, text = '', ok = 'Rendben') {
    return new Promise(res => {
      const d = document.createElement('dialog'); d.className = 'v2-modal';
      d.innerHTML = `<form method="dialog"><div class="m-body"><p class="kicker">Megerősítés</p><h2>${esc(title)}</h2><p>${esc(text)}</p></div>
        <div class="m-actions"><button class="bar-btn ghost" value="no">Mégse</button><button class="bar-btn" value="ok">${esc(ok)}</button></div></form>`;
      document.body.append(d);
      d.addEventListener('close', () => { res(d.returnValue === 'ok'); d.remove(); });
      d.showModal();
    });
  }
  window.V2 = { toast, confirm: confirmBox };

  /* ---------- Egyedi legördülő (natív select/datalist helyett): fel/le, Enter, Esc, kívülre kattintás ----------
     anchor: gomb vagy input; items(q) → [{ value, label, sub?, cat? }]; onPick(item). Input esetén gépelésre szűr. */
  function dropdown(anchor, { items, onPick, selected = () => null }) {
    const isInput = anchor.tagName === 'INPUT';
    const box = anchor.closest('.field'); box.classList.add('dd-host');
    const ul = document.createElement('ul'); ul.className = 'dd'; ul.setAttribute('role', 'listbox'); ul.id = `${anchor.id}-list`; ul.hidden = true;
    box.append(ul);
    anchor.setAttribute('aria-controls', ul.id); anchor.setAttribute('aria-expanded', 'false');
    if (isInput) { anchor.setAttribute('role', 'combobox'); anchor.setAttribute('aria-autocomplete', 'list'); }
    let list = [], active = -1;
    const paint = () => {
      ul.innerHTML = list.length ? list.map((it, i) => `<li role="option" id="${ul.id}-${i}" data-i="${i}" class="${it.cat ? `cat-${slug(it.cat)}` : ''}${i === active ? ' active' : ''}" aria-selected="${selected() === it.value}">
          <span class="sw" aria-hidden="true"></span><span>${esc(it.label)}${it.sub ? ` <small>${esc(it.sub)}</small>` : ''}</span></li>`).join('')
        : '<li class="dd-none" aria-disabled="true">Nincs találat</li>';
      anchor.setAttribute('aria-activedescendant', active >= 0 ? `${ul.id}-${active}` : '');
      ul.querySelector('.active')?.scrollIntoView({ block: 'nearest' });
    };
    const open = (all = false) => { list = items(isInput && !all ? anchor.value : ''); active = Math.max(0, list.findIndex(it => it.value === selected())); if (isInput && anchor.value && !list.some(it => it.value === anchor.value)) active = 0; ul.hidden = false; anchor.setAttribute('aria-expanded', 'true'); paint(); };
    const close = () => { ul.hidden = true; anchor.setAttribute('aria-expanded', 'false'); anchor.classList.remove('is-typing'); box.querySelector('.dd-toggle')?.setAttribute('aria-expanded', 'false'); };
    const pick = i => { const it = list[i]; if (!it) return; close(); onPick(it); if (isInput) anchor.blur(); /* választás után ne villogjon a kurzor */ };
    anchor.addEventListener(isInput ? 'focus' : 'click', () => (ul.hidden || isInput ? open() : close()));
    const toggle = box.querySelector('.dd-toggle');
    toggle?.addEventListener('click', () => { if (ul.hidden) { open(true); toggle.setAttribute('aria-expanded', 'true'); } else { close(); } });
    if (isInput) {
      anchor.addEventListener('input', () => { anchor.classList.add('is-typing'); open(); active = list.length ? 0 : -1; paint(); });
      anchor.addEventListener('blur', () => { anchor.classList.remove('is-typing'); close(); });
    }
    anchor.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (ul.hidden) return open(); active = (active + (e.key === 'ArrowDown' ? 1 : -1) + list.length) % list.length; paint(); }
      else if (e.key === 'Enter' && !ul.hidden && active >= 0) { e.preventDefault(); pick(active); }
      else if (e.key === 'Escape') { e.preventDefault(); close(); if (isInput) anchor.blur(); }
      else if (e.key === 'Tab') close();
    });
    ul.addEventListener('mousedown', e => e.preventDefault()); // ne vegye el a fókuszt az inputtól
    ul.addEventListener('click', e => { const li = e.target.closest('[data-i]'); if (li) pick(+li.dataset.i); });
    ul.addEventListener('mousemove', e => { const li = e.target.closest('[data-i]'); if (li && +li.dataset.i !== active) { active = +li.dataset.i; paint(); } });
    document.addEventListener('click', e => { if (!box.contains(e.target)) close(); });
    return { open, close };
  }

  /* ---------- Oldalsáv ---------- */
  const ROLE_KEY = 'fmh2-role';
  // Az oldal dönti el a szerepet (mester-* = mester, a 3 felhasználói oldal = felhasználó); máshol a tárolt érték.
  const role = page.startsWith('mester-') ? 'mester' : ['mesterek', 'hirdetes-uj', 'hirdetes-sajat'].includes(page) ? 'user'
    : localStorage.getItem(ROLE_KEY) === 'mester' ? 'mester' : 'user';
  localStorage.setItem(ROLE_KEY, role);
  const MENU = {
    user: [['mesterek.html', 'Mesterek'], ['hirdetes-sajat.html', 'Hirdetéseim']],
    mester: [['mester-hirdetesek.html', 'Hirdetések'], ['mester-munkaim.html', 'Munkáim'], ['mester-szolgaltatasaim.html', 'Szolgáltatásaim']],
  };
  const file = location.pathname.split('/').pop() || 'mesterek.html';
  const me = role === 'mester' ? ['Kovács Péter', 'Mester'] : ['Bálint Erika', 'Felhasználó'];
  document.body.insertAdjacentHTML('afterbegin', `
    <aside class="sb" aria-label="Oldalsáv">
      <a class="sb-logo" href="${MENU[role][0][0]}"><svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${ICONS.logo}</svg><span>FixMy<b>Home</b></span></a>
      <nav class="sb-nav" aria-label="Főmenü">${MENU[role].map(([h, t], i) => `<a href="${h}"${h === file ? ' aria-current="page"' : ''}><small>0${i + 1}</small><span>${t}</span></a>`).join('')}</nav>
      ${role === 'user' ? `<div class="sb-cta"><a class="bar-btn sm" href="hirdetes-uj.html"${file === 'hirdetes-uj.html' ? ' aria-current="page"' : ''}>Hirdetés feladása</a></div>` : ''}
      <div class="sb-foot">
        <div class="sb-profile"><span class="av">${initials(me[0])}</span><span><b>${me[0]}</b><small>${me[1]}</small></span></div>
        <div class="sb-role" role="group" aria-label="Szerepkör (demó)"><button data-role="user" aria-pressed="${role === 'user'}">Felhasználó</button><button data-role="mester" aria-pressed="${role === 'mester'}">Mester</button></div>
      </div>
    </aside>`);
  $$('.sb-role [data-role]').forEach(b => b.addEventListener('click', () => {
    localStorage.setItem(ROLE_KEY, b.dataset.role);
    const own = [...MENU[b.dataset.role].map(m => m[0]), ...(b.dataset.role === 'user' ? ['hirdetes-uj.html'] : [])];
    location.href = own.includes(file) ? location.href : MENU[b.dataset.role][0][0];
  }));
  const flash = sessionStorage.getItem('fmh2-flash');
  if (flash) { sessionStorage.removeItem('fmh2-flash'); setTimeout(() => toast(flash), 300); }

  /* ---------- Mesterek: keresősor + lista ⇄ térkép összekötve ---------- */
  function mesterek() {
    const sel = $('#q-trade'), town = $('#q-town'), list = $('#mlist'), count = $('#mcount');
    let trade = '', center = TOWNS.Szabadka, markers = {}, map, layer;
    dropdown(sel, {
      items: () => [{ value: '', label: 'Bármilyen' }, ...CATS.map(c => ({ value: c, label: c, cat: c }))],
      selected: () => trade,
      onPick: it => { trade = it.value; sel.textContent = it.label; sel.className = `dd-btn${it.cat ? ` cat-${slug(it.cat)}` : ''}`; render(); },
    });
    const goTown = name => { center = TOWNS[name]; town.value = name; render(); };
    dropdown(town, {
      items: q => findTowns(q).map(([hu, v]) => ({ value: hu, label: hu, sub: v[2] !== hu ? v[2] : '' })),
      selected: () => town.value,
      onPick: it => goTown(it.value),
    });
    if (window.L) {
      map = L.map('map', { zoomControl: true }).setView(center.slice(0, 2), 12);
      // Offline: csempe nélkül a CSS-rács a háttér. Az első sikertelen csempénél leválasztjuk a réteget, hogy ne próbálkozzon tovább.
      const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '&copy; OpenStreetMap', errorTileUrl: 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7' });
      let tileOk = false;
      const offline = () => { if (tileOk) return; if (map.hasLayer(tiles)) map.removeLayer(tiles); if (!$('.map-offline')) $('#map').insertAdjacentHTML('beforeend', '<span class="map-offline">Offline – alaptérkép nélkül</span>'); };
      tiles.on('tileload', () => { tileOk = true; }).on('tileerror', offline);
      if (navigator.onLine) tiles.addTo(map); else offline();
      layer = L.layerGroup().addTo(map);
    }
    const hot = (id, on, scroll) => {
      $$(`.mrow[data-id="${id}"]`).forEach(r => { r.classList.toggle('hot', on); if (on && scroll) r.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); });
      markers[id]?.getElement()?.firstChild.classList.toggle('hot', on);
    };
    function render() {
      const rows = MESTEREK.map(m => ({ m, d: km(center, [m.lat, m.lng]) })).filter(x => x.d <= 20 && (!trade || x.m.trade === trade)).sort((a, b) => a.d - b.d);
      count.textContent = `${rows.length} mester · 20 km · ${Object.keys(TOWNS).find(k => TOWNS[k] === center)}`;
      list.innerHTML = rows.length ? rows.map(({ m, d }, i) => `
        <a class="mrow cat-${slug(m.trade)}" style="--i:${i}" data-id="${m.id}" href="hirdetes-uj.html?kat=${encodeURIComponent(m.trade)}" title="Ajánlatot kérek tőle">
          <span class="sq">${icon(m.trade)}</span>
          <span><h3>${esc(m.name)}</h3><span class="meta">${esc(m.trade)} · ${esc(m.town)}</span><span class="meta">${esc(m.price)} · <span class="rating">Még nincs értékelés</span></span></span>
          <span class="dist">${fmt(d)}<small>KM</small></span><span class="go" aria-hidden="true">→</span>
        </a>`).join('')
        : `<div class="mempty"><p class="kicker">Nincs találat</p><h3>Nincs ilyen mester a közelben.</h3><p class="muted">Válassz másik szakmát vagy települést – vagy add fel a hirdetésed, és szólunk a környékbelieknek.</p><a class="link-arrow" href="hirdetes-uj.html">Hirdetés feladása</a></div>`;
      if (!map) return;
      layer.clearLayers(); markers = {};
      L.marker(center.slice(0, 2), { icon: L.divIcon({ className: '', html: '<div class="me"></div>', iconSize: [16, 16] }), title: 'Itt vagy' }).addTo(layer);
      rows.forEach(({ m }) => {
        const mk = L.marker([m.lat, m.lng], { title: m.name, icon: L.divIcon({ className: '', html: `<div class="pin">${initials(m.name)}</div>`, iconSize: [30, 30], iconAnchor: [15, 15] }) }).addTo(layer);
        mk.on('mouseover', () => hot(m.id, true, true)).on('mouseout', () => hot(m.id, false)).on('click', () => location.href = `hirdetes-uj.html?kat=${encodeURIComponent(m.trade)}`);
        markers[m.id] = mk;
      });
      const pts = rows.map(({ m }) => [m.lat, m.lng]).concat([center.slice(0, 2)]);
      map.fitBounds(L.latLngBounds(pts).pad(.15), { maxZoom: 14 });
    }
    list.addEventListener('mouseover', e => { const r = e.target.closest('.mrow'); if (r) hot(r.dataset.id, true); });
    list.addEventListener('mouseout', e => { const r = e.target.closest('.mrow'); if (r) hot(r.dataset.id, false); });
    $('#search').addEventListener('submit', e => {
      e.preventDefault();
      town.blur();
      const hit = findTowns(town.value)[0];
      if (!town.value.trim() || !hit) return toast('Ismeretlen település – próbáld: Szabadka, Zenta (Senta), Óbecse (Bečej)…');
      goTown(hit[0]);
    });
    render();
  }

  /* ---------- Hirdetés feladása: szekciók + élő előnézet ---------- */
  function hirdetesUj() {
    const f = $('#ad-form'), pv = $('#preview'), files = [];
    let cat = CATS.includes(params.get('kat')) ? params.get('kat') : '', town = '';
    $('#tiles').innerHTML = CATS.map(c => `<button type="button" class="tile cat-${slug(c)}" data-cat="${c}" aria-pressed="${c === cat}"><span class="sq">${icon(c)}</span>${c}</button>`).join('');
    $('#towns').innerHTML = Object.entries(TOWNS).map(([t, v]) => `<button type="button" data-town="${t}" aria-pressed="false">${t}${v[2] !== t ? `<small>${v[2]}</small>` : ''}</button>`).join('');
    const draw = () => {
      const t = f.title.value.trim(), d = f.desc.value.trim();
      pv.className = `preview${cat ? ` cat-${slug(cat)}` : ''}`;
      pv.innerHTML = `
        <div style="display:flex;justify-content:space-between;gap:10px;align-items:center">${cat ? `<span class="trade">${cat}</span>` : '<span class="trade pv-empty">Szakma?</span>'}<span class="tag tag-open">Nyitott</span></div>
        <h3 class="${t ? '' : 'pv-empty'}">${esc(t || 'A hirdetésed címe')}</h3>
        <p class="pv-desc ${d ? '' : 'pv-empty'}">${esc(d || 'Itt jelenik meg a leírás: mi a gond, mióta, mekkora a munka.')}</p>
        ${files.length ? `<div class="pv-imgs">${files.slice(0, 6).map(s => `<img src="${s}" alt="">`).join('')}</div>` : ''}
        <p class="mono muted" style="margin:0">${town ? `${town} · ` : ''}Most · 0 jelentkező</p>`;
    };
    $('#tiles').addEventListener('click', e => { const b = e.target.closest('[data-cat]'); if (!b) return; cat = b.dataset.cat; $$('#tiles [data-cat]').forEach(x => x.setAttribute('aria-pressed', x === b)); clearErr('cat'); draw(); });
    $('#towns').addEventListener('click', e => { const b = e.target.closest('[data-town]'); if (!b) return; town = b.dataset.town; $$('#towns [data-town]').forEach(x => x.setAttribute('aria-pressed', x === b)); clearErr('town'); draw(); });
    f.addEventListener('input', e => { clearErr(e.target.name); draw(); });
    const drop = $('#drop'), thumbs = $('#thumbs');
    const add = list => [...list].filter(x => x.type.startsWith('image/')).forEach(file => { const r = new FileReader(); r.onload = () => { files.push(r.result); drawThumbs(); draw(); }; r.readAsDataURL(file); });
    const drawThumbs = () => { thumbs.innerHTML = files.map((s, i) => `<figure><img src="${s}" alt="Kép ${i + 1}"><button type="button" data-del="${i}" aria-label="Kép törlése">×</button></figure>`).join(''); };
    thumbs.addEventListener('click', e => { const b = e.target.closest('[data-del]'); if (b) { files.splice(+b.dataset.del, 1); drawThumbs(); draw(); } });
    drop.addEventListener('click', () => f.images.click());
    drop.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); f.images.click(); } });
    drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('drag'); });
    drop.addEventListener('dragleave', () => drop.classList.remove('drag'));
    drop.addEventListener('drop', e => { e.preventDefault(); drop.classList.remove('drag'); add(e.dataTransfer.files); });
    f.images.addEventListener('change', () => { add(f.images.files); f.images.value = ''; });
    function setErr(key, msg) { const box = $(`[data-err="${key}"]`); box.classList.add('has-err'); box.insertAdjacentHTML('beforeend', `<p class="err" data-errmsg="${key}">${msg}</p>`); }
    function clearErr(key) { const box = $(`[data-err="${key}"]`); if (!box) return; box.classList.remove('has-err'); $$(`[data-errmsg="${key}"]`).forEach(x => x.remove()); }
    f.addEventListener('submit', async e => {
      e.preventDefault();
      ['title', 'desc', 'cat', 'town'].forEach(clearErr);
      const errs = [];
      if (!f.title.value.trim()) errs.push(['title', 'Adj címet a hirdetésnek.']);
      if (!f.desc.value.trim()) errs.push(['desc', 'Írj pár mondatot a problémáról.']);
      if (!cat) errs.push(['cat', 'Válaszd ki, milyen szakember kell.']);
      if (!town) errs.push(['town', 'Válaszd ki a települést.']);
      if (errs.length) { errs.forEach(([k, m]) => setErr(k, m)); $(`[data-err="${errs[0][0]}"]`).scrollIntoView({ behavior: 'smooth', block: 'center' }); return; }
      const imgs = await Promise.all(files.slice(0, 4).map(shrink));
      const ad = { title: f.title.value.trim(), desc: f.desc.value.trim(), cat, town, images: imgs, status: 'open', chosen: null, created: Date.now(), applicants: defaultApplicants(cat) };
      try { localStorage.setItem('fmh2-ad', JSON.stringify(ad)); } catch { ad.images = []; localStorage.setItem('fmh2-ad', JSON.stringify(ad)); }
      sessionStorage.setItem('fmh2-flash', 'Közzétéve – a környékbeli mesterek értesítést kapnak.');
      location.href = 'hirdetes-sajat.html';
    });
    draw();
  }
  function shrink(src) {
    return new Promise(res => { const img = new Image(); img.onload = () => { const s = Math.min(1, 520 / Math.max(img.width, img.height)), c = document.createElement('canvas'); c.width = img.width * s; c.height = img.height * s; c.getContext('2d').drawImage(img, 0, 0, c.width, c.height); res(c.toDataURL('image/jpeg', .72)); }; img.onerror = () => res(src); img.src = src; });
  }
  const defaultApplicants = cat => [
    { name: 'Tóth Gábor', trade: cat || 'Vízszerelő', msg: 'Holnap délelőtt ki tudok menni felmérni, a felső lakásba is be kellene jutni.', dist: 1.8, phone: '+381 60 211 4433' },
    { name: 'Kiss Ferenc', trade: cat || 'Vízszerelő', msg: 'Hasonló munkát már sokat csináltam, csütörtöktől ráérek.', dist: 2.6, phone: '+381 64 990 1020' },
    { name: 'Horváth Ernő', trade: 'Burkoló', msg: 'Ha a csempét is bontani kell, azt vállalom, szakemberrel együtt dolgozom.', dist: 2.7, phone: '+381 63 555 7788' },
  ].map(a => ({ ...a, status: 'pending' }));

  /* ---------- Saját hirdetés: idővonal + galéria + sticky jelentkezők ---------- */
  function hirdetesSajat() {
    let ad;
    try { ad = JSON.parse(localStorage.getItem('fmh2-ad')); } catch { ad = null; }
    ad ||= { title: 'Beázik a fürdőszoba mennyezete', desc: 'A felső szomszédnál valószínűleg egy cső szivárog, nálunk sárga folt van a mennyezeten és csöpög. Panellakás, 3. emelet.', cat: 'Vízszerelő', town: 'Szabadka', images: [], status: 'open', chosen: null, created: Date.now() - 20 * 3600e3, applicants: defaultApplicants('Vízszerelő') };
    const save = () => localStorage.setItem('fmh2-ad', JSON.stringify(ad));
    const root = $('#own');
    const ago = t => { const h = Math.round((Date.now() - t) / 3600e3); return h < 1 ? 'most' : h < 24 ? `${h} órája` : `${Math.round(h / 24)} napja`; };
    const draw = () => {
      const s = ad.status, idx = ['open', 'in_progress', 'closed'].indexOf(s);
      const steps = [['Nyitott', 'A mesterek jelentkezhetnek'], ['Folyamatban', 'Kiválasztottad a mestert'], ['Lezárva', 'A munka elkészült']];
      const imgs = ad.images.length ? ad.images.map(src => `<img src="${src}" alt="">`) : [1, 2, 3].map(() => `<div class="ph">${icon(ad.cat)}</div>`);
      const ch = ad.chosen != null ? ad.applicants[ad.chosen] : null;
      root.innerHTML = `
        <p class="kicker">Hirdetéseim · ${esc(ad.cat)}</p>
        <h1 class="huge">${esc(ad.title.replace(/[.\s]+$/, ''))}</h1>
        <div class="timeline ${s === 'withdrawn' ? 'withdrawn' : ''}" aria-label="Állapot">
          ${steps.map(([b, sm], i) => `<div class="step ${s === 'withdrawn' ? '' : i < idx || s === 'closed' ? 'done' : i === idx ? 'current' : ''}"><b>${b}</b><small>${s === 'withdrawn' && i === 0 ? 'Visszavonva' : sm}</small></div>`).join('')}
        </div>
        <div class="ad-grid">
          <div>
            <div class="gallery">${imgs.join('')}</div>
            <p class="ad-desc">${esc(ad.desc)}</p>
            <div class="ad-meta cat-${slug(ad.cat)}">
              <div><span class="trade">Szakma</span><b>${esc(ad.cat)}</b></div>
              <div><span class="mono">Hol</span><b>${esc(ad.town)}</b></div>
              <div><span class="mono">Feladva</span><b>${ago(ad.created)}</b></div>
            </div>
            <p style="margin-top:28px">${s === 'open' ? '<button class="link-arrow" data-withdraw>Hirdetés visszavonása</button>' : '<a class="link-arrow" href="hirdetes-uj.html">Új hirdetés feladása</a>'}</p>
          </div>
          <aside class="side">
            ${ch ? `
              <div class="side-head"><span class="mono">Kiválasztott mester</span><span class="tag tag-accepted">Elfogadva</span></div>
              <div class="chosen cat-${slug(ch.trade)}">
                <span class="sq">${icon(ch.trade)}</span>
                <div class="big">${esc(ch.name)}</div>
                <span class="trade">${esc(ch.trade)} · ${fmt(ch.dist)} km</span>
                <p style="margin:0">„${esc(ch.msg)}”</p>
                <div class="contact"><div><span class="mono">Telefon</span><b>${esc(ch.phone)}</b></div><div><span class="mono">Időpont</span><b>Még nincs időpont</b></div></div>
              </div>
              ${s === 'in_progress' ? '<button class="bar-btn" data-close>A munka kész – Lezárás</button>' : '<button class="bar-btn" disabled>Lezárva</button>'}`
            : `
              <div class="side-head"><span class="mono">Jelentkezők</span><span class="count">${String(ad.applicants.length).padStart(2, '0')}</span></div>
              ${ad.applicants.map((a, i) => `
                <div class="app cat-${slug(a.trade)} ${a.status === 'rejected' ? 'is-rejected' : ''}" style="--i:${i}">
                  <span class="rank">${String(i + 1).padStart(2, '0')}</span>
                  <h3>${esc(a.name)} <span class="mono muted">${fmt(a.dist)} km</span></h3>
                  <div><span class="trade">${esc(a.trade)}</span> <span class="mono muted">· Még nincs értékelés</span><p>„${esc(a.msg)}”</p></div>
                  ${s === 'open' ? `<div><button class="link-arrow" data-pick="${i}">Kiválasztom</button></div>` : `<div><span class="tag tag-${a.status}">${a.status === 'rejected' ? 'Elutasítva' : 'Függőben'}</span></div>`}
                </div>`).join('')}
              <div class="side-foot"><span class="mono muted">Rangsor: távolság szerint</span></div>`}
          </aside>
        </div>`;
    };
    root.addEventListener('click', async e => {
      const pick = e.target.closest('[data-pick]');
      if (pick) {
        const a = ad.applicants[+pick.dataset.pick];
        if (!await confirmBox(`${a.name} kiválasztása`, 'A többi jelentkezést elutasítjuk, a hirdetés Folyamatban állapotba kerül.', 'Kiválasztom')) return;
        ad.applicants.forEach(x => { x.status = x === a ? 'accepted' : 'rejected'; });
        ad.chosen = +pick.dataset.pick; ad.status = 'in_progress'; save(); draw(); toast(`${a.name} kiválasztva – értesítettük.`);
      }
      if (e.target.closest('[data-close]')) {
        if (!await confirmBox('Lezárod a munkát?', 'Akkor zárd le, ha a mester elvégezte a munkát.', 'Lezárás')) return;
        ad.status = 'closed'; save(); draw(); toast('Munka lezárva. Köszönjük!');
      }
      if (e.target.closest('[data-withdraw]')) {
        if (!await confirmBox('Visszavonod a hirdetést?', 'A mesterek többé nem látják és nem jelentkezhetnek.', 'Visszavonás')) return;
        ad.status = 'withdrawn'; save(); draw(); toast('Hirdetés visszavonva.');
      }
    });
    draw();
  }

  ({ mesterek, 'hirdetes-uj': hirdetesUj, 'hirdetes-sajat': hirdetesSajat })[page]?.();
})();
