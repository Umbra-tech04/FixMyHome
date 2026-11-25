/* FixMyHome – a Django-oldalak kliensoldali része (a design/app.js-ből átemelve, kamu adatok nélkül).
   defer-rel töltődik; a téma első beállítását a base.html inline scriptje végzi (window.FMH_THEMES, localStorage „fmh-theme”).
   Hookok a markupban:
     link#theme-css + window.FMH_THEMES a [data-theme="a|b"] gombok cserélik (localStorage „fmh-theme”)
     .main-nav .nav-indicator           csúszó aktív aláhúzás a menüben
     [data-geolocate]                   gomb egy formban, benne [name=latitude] / [name=longitude] rejtett mezőkkel;
                                        alapból beküldi a formot, data-geolocate="fill" esetén csak kitölti
     #map[data-api][data-lat][data-lng][data-radius]  Leaflet-térkép a /api/ JSON-ból
     [data-view="list|map"]             nézetváltó gombok; panelek: [data-view-panel="list|map"]
     input[type=file][data-preview]     képelőnézet (a .thumbs a mező után jön létre)
     form[data-confirm="Kérdés?"]       megerősítő modal; opcionális: data-confirm-body, data-confirm-ok
     .messages li                       Django messages → toast (li class = message.tags)
     .card-list > *                     lépcsőzetes megjelenés */

(() => {
  const KEY = 'fmh-theme';
  const THEMES = window.FMH_THEMES || {};
  const theme = THEMES[localStorage.getItem(KEY)] ? localStorage.getItem(KEY) : 'a';
  window.FMH_CONFIRM = true; // a base.html natív confirm() fallbackja így nem kérdez másodszor

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const PIN = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>';
  const fmtKm = d => `${Number(d).toFixed(1).replace('.', ',')} km`;
  const initials = n => String(n).split(/\s+/).map(w => w[0] || '').join('').slice(0, 2);

  function toast(msg, level = 'success') {
    let root = $('#toasts');
    if (!root) { root = document.createElement('div'); root.id = 'toasts'; root.setAttribute('aria-live', 'polite'); document.body.append(root); }
    const t = document.createElement('div');
    t.className = `toast toast-${level}`;
    t.innerHTML = `<span>${esc(msg)}</span>`;
    root.append(t);
    setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 300); }, level === 'error' ? 6000 : 3600);
  }

  function modal({ title, body = '', ok = 'Rendben', okClass = 'btn-primary', cancel = 'Mégse' }) {
    return new Promise(resolve => {
      const d = document.createElement('dialog');
      d.className = 'modal';
      d.innerHTML = `<form method="dialog"><div class="modal-body"><h2>${esc(title)}</h2>${body ? `<p>${esc(body)}</p>` : ''}</div>
        <div class="modal-actions"><button class="btn btn-secondary" value="cancel" formnovalidate>${esc(cancel)}</button><button class="btn ${okClass}" value="ok">${esc(ok)}</button></div></form>`;
      document.body.append(d);
      d.addEventListener('close', () => { resolve(d.returnValue === 'ok'); setTimeout(() => d.remove(), 0); });
      d.showModal();
    });
  }

  const stagger = () => $$('.card-list').forEach(l => $$(':scope > *', l).forEach((c, i) => c.style.setProperty('--i', i)));

  function initTheme() {
    $$('[data-theme]:is(button, a)').forEach(b => {
      b.setAttribute('aria-pressed', b.dataset.theme === theme);
      b.addEventListener('click', e => {
        e.preventDefault();
        localStorage.setItem(KEY, b.dataset.theme);
        const link = document.getElementById('theme-css');
        if (link && THEMES[b.dataset.theme]) {
          // Új betűtípus = új menüszélességek: töltés után a csúszó aláhúzást újra kell igazítani.
          link.addEventListener('load', () => document.fonts.ready.then(() => window.dispatchEvent(new Event('fmh:theme'))), { once: true });
          link.href = THEMES[b.dataset.theme];
        }
        document.documentElement.dataset.theme = b.dataset.theme;
        $$('[data-theme]:is(button, a)').forEach(x => x.setAttribute('aria-pressed', x === b));
      });
    });
  }

  function initMessages() {
    $$('.messages').forEach(ul => {
      $$('li', ul).forEach((li, i) => setTimeout(() => toast(li.textContent.trim(), /error|warning/.test(li.className) ? 'error' : 'success'), 250 + i * 150));
      ul.remove();
    });
  }

  function initGeolocate() {
    $$('[data-geolocate]').forEach(btn => {
      const form = btn.closest('form');
      if (!form) return;
      const lat = form.elements.latitude, lng = form.elements.longitude;
      const text = $('input[list=cities]', form) || $('input:not([type=hidden]):not([type=submit])', form);
      // Kézzel beírt településnél a korábbi GPS-koordináta ne nyerjen.
      text?.addEventListener('input', () => { if (lat) lat.value = ''; if (lng) lng.value = ''; });
      btn.addEventListener('click', e => {
        e.preventDefault();
        const fail = msg => { toast(msg, 'error'); text?.focus(); };
        if (!navigator.geolocation || !lat || !lng) return fail('A helymeghatározás nem elérhető – írd be a települést.');
        btn.disabled = true;
        navigator.geolocation.getCurrentPosition(
          p => {
            lat.value = p.coords.latitude.toFixed(6); lng.value = p.coords.longitude.toFixed(6);
            if (btn.dataset.geolocate === 'fill') { btn.disabled = false; toast('Megvan a helyed – ne felejtsd el menteni.'); }
            else form.submit();
          },
          () => { btn.disabled = false; fail('Nem kaptunk helyengedélyt – írd be a települést vagy irányítószámot.'); },
          { timeout: 10000, maximumAge: 300000 });
      });
    });
  }

  function masterCard(m) {
    return `<div class="card">
      <div class="card-head"><span class="avatar" aria-hidden="true">${esc(initials(m.name))}</span>
        <div style="flex:1"><h3>${esc(m.name)}</h3>
          <div class="row" style="gap:8px"><span class="chip chip-trade">${esc(m.profession)}</span><span class="pill-distance">${PIN}${fmtKm(m.distance_km)}</span></div></div>
      </div>
      <div class="card-meta"><span>${PIN}${esc(m.city)}</span><span class="rating-none">Még nincs értékelés</span></div>
    </div>`;
  }

  function initMap() {
    const el = $('#map[data-api]');
    if (!el || !window.L) return;
    let wrap = el.closest('.map-wrap');
    if (!wrap) { wrap = document.createElement('div'); wrap.className = 'map-wrap'; el.before(wrap); wrap.append(el); }
    wrap.insertAdjacentHTML('beforeend', '<div class="sheet"><button type="button" class="btn btn-ghost btn-sm sheet-close" aria-label="Bezárás">✕</button><div class="sheet-body"></div></div>');
    const sheet = $('.sheet', wrap);
    $('.sheet-close', sheet).onclick = () => sheet.classList.remove('open');

    const api = new URL(el.dataset.api, location.href);
    // A data-lat/lng/radius az irányadó; ha a data-api-ban már benne vannak, azokat felülírjuk ugyanazzal.
    if (el.dataset.lat) api.searchParams.set('lat', el.dataset.lat);
    if (el.dataset.lng) api.searchParams.set('lng', el.dataset.lng);
    if (el.dataset.radius) api.searchParams.set('r', el.dataset.radius);
    const center = [parseFloat(api.searchParams.get('lat')), parseFloat(api.searchParams.get('lng'))];
    let map = null;
    const draw = () => {
      if (map) return map.invalidateSize();
      if (!wrap.offsetParent) return; // rejtett panelben a Leaflet nem tud méretet számolni
      map = L.map(el).setView(Number.isFinite(center[0]) ? center : [46.1003, 19.6656], 12);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '&copy; OpenStreetMap' }).addTo(map);
      map.on('click', () => sheet.classList.remove('open'));
      fetch(api, { headers: { Accept: 'application/json' }, credentials: 'same-origin' })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(data => {
          const color = getComputedStyle(document.body).getPropertyValue('--primary').trim();
          if (Number.isFinite(center[0])) {
            L.marker(center, { title: 'Itt vagy', icon: L.divIcon({ className: '', html: '<div class="map-me"></div>', iconSize: [18, 18] }) }).addTo(map);
            const circle = L.circle(center, { radius: data.radius_km * 1000, color, weight: 2, fillOpacity: .06 }).addTo(map);
            map.fitBounds(circle.getBounds());
          }
          data.masters.forEach(m => {
            if (m.lat == null || m.lng == null) return;
            const mk = L.marker([m.lat, m.lng], { title: m.name, icon: L.divIcon({ className: '', html: `<div class="map-pin"><span>${esc(initials(m.name))}</span></div>`, iconSize: [38, 38], iconAnchor: [19, 38] }) }).addTo(map);
            mk.on('click', ev => {
              L.DomEvent.stopPropagation(ev);
              $$('.map-pin.active', el).forEach(p => p.classList.remove('active'));
              mk.getElement().firstChild.classList.add('active');
              $('.sheet-body', sheet).innerHTML = masterCard(m);
              sheet.classList.add('open');
            });
          });
          if (!data.masters.length && data.suggest_radius) toast(`Ebben a körzetben nincs mester – próbáld ${data.suggest_radius} km-rel.`, 'error');
        })
        .catch(() => toast('A térkép adatai most nem tölthetők be.', 'error'));
    };

    const buttons = $$('[data-view]');
    const show = view => {
      buttons.forEach(b => b.setAttribute('aria-pressed', b.dataset.view === view));
      $$('[data-view-panel]').forEach(p => { p.hidden = p.dataset.viewPanel !== view; });
      localStorage.setItem('fmh-view', view);
      if (view === 'map') draw();
    };
    buttons.forEach(b => b.addEventListener('click', () => show(b.dataset.view)));
    if (buttons.length) show(localStorage.getItem('fmh-view') === 'map' ? 'map' : 'list');
    else draw();
  }

  function initPreview() {
    $$('input[type=file][data-preview]').forEach(input => {
      const thumbs = document.createElement('div');
      thumbs.className = 'thumbs';
      input.after(thumbs);
      let urls = [];
      const render = () => {
        urls.forEach(URL.revokeObjectURL);
        urls = [...input.files].map(f => URL.createObjectURL(f));
        thumbs.innerHTML = urls.map((u, i) => `<figure><img src="${u}" alt="${esc(input.files[i].name)}"><button type="button" data-del="${i}" aria-label="Kép eltávolítása">×</button></figure>`).join('');
      };
      input.addEventListener('change', render);
      thumbs.addEventListener('click', e => {
        const b = e.target.closest('[data-del]');
        if (!b) return;
        const dt = new DataTransfer();
        [...input.files].forEach((f, i) => { if (i !== +b.dataset.del) dt.items.add(f); });
        input.files = dt.files;
        render();
      });
    });
  }

  function initConfirm() {
    $$('form[data-confirm]').forEach(form => form.addEventListener('submit', async e => {
      if (form.dataset.confirmed) { delete form.dataset.confirmed; return; }
      e.preventDefault();
      const sub = e.submitter;
      const ok = await modal({
        title: form.dataset.confirm,
        body: form.dataset.confirmBody,
        ok: form.dataset.confirmOk || sub?.textContent.trim() || 'Rendben',
        okClass: sub?.classList.contains('btn-danger') || form.querySelector('.btn-danger') ? 'btn-danger' : 'btn-primary',
      });
      if (!ok) return;
      form.dataset.confirmed = '1';
      form.requestSubmit(sub && sub.form === form ? sub : undefined); // a submitter name/value-ja is megy
    }));
  }

  function initNav() {
    const ind = $('.main-nav .nav-indicator');
    if (!ind) return;
    const links = $$('.main-nav a'), home = links.find(a => a.hasAttribute('aria-current'));
    const move = a => { ind.style.opacity = a ? 1 : 0; if (a) { ind.style.width = `${a.offsetWidth}px`; ind.style.transform = `translateX(${a.offsetLeft}px)`; } };
    move(home);
    links.forEach(a => a.addEventListener('mouseenter', () => move(a)));
    $('.main-nav').addEventListener('mouseleave', () => move(home));
    document.fonts?.ready.then(() => move(home));
    window.addEventListener('fmh:theme', () => move(home));
  }

  function initProfile() {
    const prof = $('.profile');
    if (!prof) return;
    document.addEventListener('click', e => { if (!prof.contains(e.target)) prof.open = false; });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') prof.open = false; });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initTheme(); initNav(); initProfile(); initMessages(); initGeolocate(); initMap(); initPreview(); initConfirm(); stagger();
  });
  window.FixMyHome = { toast, modal };
})();
