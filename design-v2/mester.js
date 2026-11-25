/* FixMyHome V2 – mester-oldalak: hirdetés-tábla (accordion + jelentkezés) és kanban (animált lezárás). Kamu adatok, Django nélkül. */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const slug = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const km = d => d.toFixed(1).replace('.', ',');

  /* ---------- 1) Hirdetés-tábla ---------- */
  const ADS = [
    { id: 1, trade: 'Villanyszerelő', title: 'Nem működik a konnektor a nappaliban', desc: 'Két konnektor nem ad áramot, a biztosíték rendben van. Panellakás, 3. emelet.', town: 'Szabadka', when: '2 órája', dist: 0.4, images: 2 },
    { id: 2, trade: 'Villanyszerelő', title: 'Kiégett a konyhai biztosíték', desc: 'Tegnap este óta mindig lecsap, ha bekapcsolom a vízforralót.', town: 'Szabadka', when: '5 órája', dist: 1.8, images: 1 },
    { id: 3, trade: 'Villanyszerelő', title: 'Csillár felszerelése a nappaliba', desc: 'Megvan a lámpa, csak fel kellene szerelni. 2,8 m a belmagasság.', town: 'Palics', when: '1 napja', dist: 7.8, images: 1 },
    { id: 4, trade: 'Villanyszerelő', title: 'Új konnektorok a gyerekszobába (3 db)', desc: 'Falon kívüli kábelezés is jó, a lényeg, hogy biztonságos legyen.', town: 'Palics', when: '2 napja', dist: 8.6, images: 0 },
    { id: 5, trade: 'Villanyszerelő', title: 'Kültéri lámpák bekötése a teraszon', desc: 'Négy fali lámpa, a kábel már ki van húzva, csak bekötés kell.', town: 'Topolya', when: '3 napja', dist: 31.9, images: 3 },
    { id: 6, trade: 'Villanyszerelő', title: 'Villanyóra-szekrény cseréje', desc: 'Régi, rozsdás mérőszekrény cseréje az előírások szerint.', town: 'Zenta', when: '4 napja', dist: 38.0, images: 2 },
  ];
  const applied = new Map(); // id -> üzenet

  function renderBoard() {
    const board = $('#board');
    const radius = +$('[data-radius][aria-pressed="true"]').dataset.radius;
    const list = ADS.filter(a => a.dist <= radius);
    $('#count').textContent = `${list.length} NYITOTT HIRDETÉS · ${radius} KM`;
    board.innerHTML = list.length ? list.map((a, i) => `
      <li class="board-row cat-${slug(a.trade)}${applied.has(a.id) ? ' applied' : ''}" style="--i:${i}" data-id="${a.id}">
        <div class="row-head" role="button" tabindex="0" aria-expanded="false" aria-controls="panel-${a.id}">
          <div class="row-dist">${km(a.dist)}<small>KM</small></div>
          <div class="row-main"><span class="row-trade">${esc(a.trade)}</span><h2 class="row-title">${esc(a.title)}</h2><p class="row-desc">${esc(a.desc)}</p></div>
          <div class="row-meta">${esc(a.town)}<br>${esc(a.when)}</div>
          ${applied.has(a.id) ? '<span class="bar-btn is-done">JELENTKEZTÉL</span>' : '<span class="bar-btn" aria-hidden="true">JELENTKEZEM</span>'}
        </div>
        <div class="row-panel" id="panel-${a.id}"><div>
          <div class="panel-inner">
            <div class="panel-gallery">${a.images ? Array.from({ length: a.images }, () => '<span role="img" aria-label="Kép a hirdetéshez"></span>').join('') : '<p>NINCS CSATOLT KÉP.</p>'}<p>${esc(a.desc)}</p></div>
            ${applied.has(a.id)
              ? `<div class="panel-form"><label>A te üzeneted</label><p>„${esc(applied.get(a.id))}”</p><span class="mono-tag">FÜGGŐBEN</span></div>`
              : `<form class="panel-form" novalidate><label for="msg-${a.id}">Rövid üzenet az ügyfélnek</label><textarea id="msg-${a.id}" maxlength="300" placeholder="Pl. Holnap délután ki tudok menni felmérni."></textarea><button class="bar-btn" type="submit">KÜLDÉS</button></form>`}
          </div>
        </div></div>
      </li>`).join('') : `<li class="empty">${radius} KM-EN BELÜL NINCS NYITOTT HIRDETÉS A SZAKMÁDBAN.</li>`;
  }

  function initBoard() {
    const board = $('#board');
    $$('[data-radius]').forEach(b => b.addEventListener('click', () => {
      $$('[data-radius]').forEach(x => x.setAttribute('aria-pressed', x === b));
      renderBoard();
    }));
    const toggle = head => {
      const row = head.closest('.board-row'), open = !row.classList.contains('open');
      $$('.board-row.open', board).forEach(r => { r.classList.remove('open'); $('.row-head', r).setAttribute('aria-expanded', 'false'); });
      row.classList.toggle('open', open);
      head.setAttribute('aria-expanded', open);
      if (open) setTimeout(() => $('textarea', row)?.focus(), 250);
    };
    board.addEventListener('click', e => { const head = e.target.closest('.row-head'); if (head) toggle(head); });
    board.addEventListener('keydown', e => {
      const head = e.target.closest('.row-head');
      if (head && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); toggle(head); }
    });
    board.addEventListener('submit', e => {
      e.preventDefault();
      const form = e.target, row = form.closest('.board-row'), text = $('textarea', form).value.trim();
      $('.field-error', form)?.remove();
      if (!text) { form.insertAdjacentHTML('beforeend', '<p class="field-error" role="alert">Írj pár szót az ügyfélnek.</p>'); return $('textarea', form).focus(); }
      applied.set(+row.dataset.id, text);
      row.classList.remove('open');
      setTimeout(() => { renderBoard(); $(`[data-id="${row.dataset.id}"] .row-head`)?.focus(); }, 350); // előbb csukódjon be a panel
    });
    renderBoard();
  }

  /* ---------- 2) Kanban ---------- */
  const JOBS = [
    { trade: 'Villanyszerelő', client: 'Bálint Erika', place: 'Szabadka, Ősz utca 12.', work: 'Konyhai áramkör hibakeresése és biztosíték csere', status: 'in_progress' },
    { trade: 'Villanyszerelő', client: 'Szekeres Antal', place: 'Palics, Park utca 3.', work: 'Kültéri lámpák bekötése a teraszon', status: 'in_progress' },
    { trade: 'Villanyszerelő', client: 'Pásztor Júlia', place: 'Szabadka, Zentai út 8.', work: 'Három új konnektor a gyerekszobába', status: 'in_progress' },
    { trade: 'Villanyszerelő', client: 'Vörös Ottó', place: 'Szabadka, Zentai út 45.', work: 'Villanyóra-szekrény cseréje', status: 'done' },
  ];

  const jobCard = (j, i) => `
    <li class="job cat-${slug(j.trade)}" style="--i:${i}">
      <p class="who">${esc(j.client)}</p>
      <h3>${esc(j.work)}</h3>
      <p class="where">${esc(j.place)}</p>
      <div class="actions"><span class="mono-tag">MÉG NINCS IDŐPONT</span><button type="button" class="bar-btn sm" data-close>LEZÁRÁS</button></div>
    </li>`;

  function counts() {
    $$('[data-count]').forEach(n => { n.textContent = $$(`[data-col="${n.dataset.count}"] .job`).length; });
    $$('.col-body').forEach(col => {
      $('.col-empty', col)?.remove();
      if (!$('.job', col)) col.insertAdjacentHTML('beforeend', `<li class="col-empty">${col.dataset.col === 'done' ? 'MÉG NINCS LEZÁRT MUNKA.' : 'NINCS FOLYAMATBAN LÉVŐ MUNKA.'}</li>`);
    });
  }

  function initKanban() {
    ['in_progress', 'done'].forEach(s => {
      $(`[data-col="${s}"]`).innerHTML = JOBS.filter(j => j.status === s).map(jobCard).join('');
    });
    counts();
    $('.kanban').addEventListener('click', e => {
      const btn = e.target.closest('[data-close]'); if (!btn) return;
      const card = btn.closest('.job'), target = $('[data-col="done"]');
      // FLIP: régi hely → új hely, a kártya átcsúszik a Lezárva oszlopba.
      const first = card.getBoundingClientRect();
      card.style.animation = 'none';
      target.prepend(card);
      const last = card.getBoundingClientRect();
      counts();
      card.animate([
        { transform: `translate(${first.left - last.left}px, ${first.top - last.top}px)`, boxShadow: '12px 12px 0 #0B0B0B' },
        { transform: 'translate(0, 0)', boxShadow: '0 0 0 #0B0B0B' },
      ], { duration: matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 650, easing: 'cubic-bezier(.2,.8,.2,1)' });
      $('h2', target.closest('.col'))?.focus?.();
    });
  }

  /* ---------- 3) Szolgáltatásaim ---------- */
  const TRADES = ['Villanyszerelő', 'Vízszerelő', 'Festő', 'Asztalos', 'Burkoló', 'Lakatos'];
  // Pontos ár: összeg (din) + egység + opcionális "-tól". A megjelenítés ezres tagolással: 3 500 DIN / ÓRÁTÓL.
  const UNIT = { hour: '/ ÓRA', m2: '/ M²', visit: '/ ALKALOM', job: '/ MUNKA' };
  const UNIT_FROM = { hour: '/ ÓRÁTÓL', m2: '/ M²-TŐL', visit: '/ ALKALOMTÓL', job: '/ MUNKÁTÓL' };
  const PRICE_MIN = 100, PRICE_MAX = 1000000;
  const thousands = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '\u00a0');
  const priceText = s => `${thousands(s.amount)} DIN ${(s.from ? UNIT_FROM : UNIT)[s.unit]}`;
  // null: üres; NaN: nem egész szám; különben az összeg. A szóközt (ezres tagolás) elfogadjuk.
  const parseAmount = raw => {
    const t = String(raw).replace(/[\s\u00a0\u202f]/g, '');
    if (!t) return null;
    return /^\d+$/.test(t) ? Number(t) : NaN;
  };
  let services = [
    { id: 1, name: 'Háztartási villanyszerelés', trade: 'Villanyszerelő', desc: 'Konnektorok, kapcsolók, lámpák szerelése, hibakeresés.', amount: 3500, unit: 'hour', from: true, area: 'Szabadka és 10 km', active: true },
    { id: 2, name: 'Biztosítéktábla csere', trade: 'Villanyszerelő', desc: 'Régi olvadóbiztosítékos tábla cseréje kismegszakítósra.', amount: 15000, unit: 'job', from: false, area: 'Szabadka, Palics', active: true },
    { id: 3, name: 'Okosotthon-kapcsolók telepítése', trade: 'Villanyszerelő', desc: 'Wi-Fi-s kapcsolók és redőnyvezérlők beszerelése, beállítása.', amount: 5000, unit: 'visit', from: true, area: 'Szabadka', active: false },
  ];
  let editing = null;
  const toast = msg => window.V2?.toast?.(msg);

  const svcRow = (s, i) => `
    <li class="svc-row cat-${slug(s.trade)}${s.active ? '' : ' paused'}${editing === s.id ? ' editing' : ''}" style="--i:${i}" data-id="${s.id}">
      <div><span class="row-trade">${esc(s.trade)}</span><h3>${esc(s.name)}</h3><p class="svc-meta"><b>${esc(priceText(s))}</b> · ${esc(s.area)}</p></div>
      <div class="svc-side">
        <button type="button" class="switch" role="switch" aria-checked="${s.active}" data-toggle><span class="knob" aria-hidden="true"></span>${s.active ? 'KÖZZÉTÉVE' : 'SZÜNETEL'}</button>
        <div class="svc-actions"><button type="button" class="link-arrow" data-edit>SZERKESZTÉS</button><button type="button" class="svc-del" data-del>TÖRLÉS</button></div>
      </div>
    </li>`;

  function renderServices() {
    $('#svc-list').innerHTML = services.length ? services.map(svcRow).join('') : '<li class="empty">MÉG NINCS SZOLGÁLTATÁSOD – A JOBB OLDALI ŰRLAPPAL HIRDESS EGYET.</li>';
    requestAnimationFrame(() => $('#svc-list').classList.add('ready'));  // a felcsúszás csak az első rajzolásnál
    const active = services.filter(s => s.active).length;
    $('#svc-count').textContent = `${services.length} SZOLGÁLTATÁS · ${active} KÖZZÉTÉVE`;
  }

  function fillForm(s) {
    const f = $('#svc-form');
    editing = s ? s.id : null;
    f.reset();
    clearErrors(f);
    if (s) {
      f.name.value = s.name; f.desc.value = s.desc; f.area.value = s.area; f.trade.value = s.trade;
      f.price.value = thousands(s.amount); f.unit.value = s.unit; f.from.checked = s.from;
    }
    updatePreview();
    $('#svc-form-title').textContent = s ? 'SZOLGÁLTATÁS SZERKESZTÉSE' : 'ÚJ SZOLGÁLTATÁS';
    $('#svc-submit').textContent = s ? 'MENTÉS' : 'KÖZZÉTÉTEL';
    $('#svc-cancel').hidden = !s;
    renderServices();
  }

  function priceError(raw) {
    const n = parseAmount(raw);
    if (n === null) return 'Add meg az árat.';
    if (Number.isNaN(n)) return 'Csak egész számot írj (pl. 3500).';
    if (n < PRICE_MIN || n > PRICE_MAX) return 'Az ár 100 és 1 000 000 din között legyen.';
    return '';
  }
  function updatePreview() {
    const f = $('#svc-form'), n = parseAmount(f.price.value);
    $('#price-preview').textContent = n && !Number.isNaN(n) ? `Így látszik: ${priceText({ amount: n, unit: f.unit.value, from: f.from.checked })}` : '';
  }

  const clearErrors = f => { $$('.err', f).forEach(e => e.remove()); $$('.has-err', f).forEach(e => e.classList.remove('has-err')); };
  // Mezőnként egy szabály: '' = rendben, különben a hibaüzenet. A beküldés és az élő újraellenőrzés is ezt használja.
  const RULES = {
    name: f => f.name.value.trim() ? '' : f.name.dataset.msg,
    trade: f => f.trade.value ? '' : 'Válassz szakmát.',
    desc: f => f.desc.value.trim() ? '' : f.desc.dataset.msg,
    price: f => priceError(f.price.value),
    area: f => f.area.value.trim() ? '' : f.area.dataset.msg,
  };
  const fieldOf = (f, name) => (name === 'trade' ? $('#trade-tiles') : f[name]).closest('.field');

  function showError(f, name) {
    const field = fieldOf(f, name), msg = RULES[name](f);
    $('.err', field)?.remove();
    field.classList.toggle('has-err', !!msg);
    if (msg) field.insertAdjacentHTML('beforeend', `<p class="err" role="alert">${esc(msg)}</p>`);
    return msg;
  }

  function validate(f) {
    const bad = Object.keys(RULES).filter(name => showError(f, name));
    if (bad.length) fieldOf(f, bad[0]).querySelector('input, textarea')?.focus();
    return !bad.length;
  }

  function initServices() {
    const f = $('#svc-form'), list = $('#svc-list');
    $('#trade-tiles').innerHTML = TRADES.map(t => `<label class="cat-${slug(t)}"><input type="radio" name="trade" value="${t}"><span>${t}</span></label>`).join('');
    f.addEventListener('submit', e => {
      e.preventDefault();
      if (!validate(f)) return;
      const data = { name: f.name.value.trim(), trade: f.trade.value, desc: f.desc.value.trim(), area: f.area.value.trim(),
                     amount: parseAmount(f.price.value), unit: f.unit.value, from: f.from.checked };
      if (editing) Object.assign(services.find(s => s.id === editing), data);
      else services.unshift({ id: Date.now(), active: true, ...data });
      toast(editing ? 'Változások mentve.' : 'Szolgáltatás közzétéve.');
      fillForm(null);
    });
    $('#svc-cancel').addEventListener('click', () => fillForm(null));
    f.addEventListener('input', e => { if (e.target.matches('[name=price], [name=unit], [name=from]')) updatePreview(); });
    // Ha egy mezőn már van hiba, gépelés/választás közben újraellenőrizzük: érvényesnél azonnal eltűnik.
    const recheck = e => {
      const name = e.target.name;
      if (RULES[name] && fieldOf(f, name).classList.contains('has-err')) showError(f, name);
    };
    f.addEventListener('input', recheck);
    f.addEventListener('change', recheck);
    f.price.addEventListener('blur', () => { const n = parseAmount(f.price.value); if (n && !Number.isNaN(n)) f.price.value = thousands(n); });
    list.addEventListener('click', e => {
      const row = e.target.closest('.svc-row'); if (!row) return;
      const s = services.find(x => x.id === +row.dataset.id);
      if (e.target.closest('[data-toggle]')) {
        s.active = !s.active; renderServices(); toast(s.active ? 'Újra közzétéve.' : 'Szüneteltetve.');
        $(`[data-id="${s.id}"] [data-toggle]`).focus();
      } else if (e.target.closest('[data-edit]')) {
        fillForm(s); $('#s-name').focus();
      } else if (e.target.closest('[data-del]')) {
        const actions = $('.svc-actions', row);
        actions.outerHTML = '<div class="svc-confirm" role="group" aria-label="Törlés megerősítése">BIZTOS? <button type="button" class="yes" data-yes>IGEN</button><button type="button" data-no>MÉGSE</button></div>';
        $('[data-no]', row).focus();
      } else if (e.target.closest('[data-no]')) {
        renderServices();
      } else if (e.target.closest('[data-yes]')) {
        const h = row.offsetHeight;
        const anim = row.animate([{ height: `${h}px`, opacity: 1 }, { height: '0px', opacity: 0, paddingTop: '0px', paddingBottom: '0px', borderBottomWidth: '0px' }],
          { duration: matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 420, easing: 'cubic-bezier(.2,.8,.2,1)', fill: 'forwards' });
        anim.onfinish = () => { services = services.filter(x => x !== s); if (editing === s.id) fillForm(null); else renderServices(); toast('Szolgáltatás törölve.'); };
      }
    });
    renderServices();
  }

  document.addEventListener('DOMContentLoaded', () => {
    if ($('#board')) initBoard();
    if ($('.kanban')) initKanban();
    if ($('#svc-list')) initServices();
  });
})();
