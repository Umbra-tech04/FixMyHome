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

  document.addEventListener('DOMContentLoaded', () => {
    if ($('#board')) initBoard();
    if ($('.kanban')) initKanban();
  });
})();
