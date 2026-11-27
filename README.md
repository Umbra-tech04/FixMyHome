# MesterKereső (FixMyHome)

Progresszív webalkalmazás, amely összeköti a műszaki problémára megoldást keresőket a közelben elérhető mesterekkel. Iskolai csapatprojekt (VTŠ), Python 3.12 + Django 5.

## Indítás 5 lépésben

```bash
git clone https://github.com/Umbra-tech04/FixMyHome.git && cd FixMyHome   # 1. klónozás
python3.12 -m venv .venv && source .venv/bin/activate                     # 2. venv (Windows: .venv\Scripts\activate)
pip install -r requirements.txt                                           # 3. függőségek
cp .env.example .env && python manage.py migrate && python manage.py seed_demo   # 4. beállítás + adatbázis + bemutató adatok
python manage.py runserver                                                # 5. indítás: http://127.0.0.1:8000
```

A projekt Python 3.12-vel készül. Ubuntu/Debian alatt a venvhez kell a `python3.12-venv` csomag (`sudo apt install python3.12-venv`).

> ⚠️ A `seed_demo` minden fiókjának jelszava `test1234`. Csak helyi gépen futtasd; **éles vagy alagúton elérhető környezetben tilos**.

Admin felülethez: `python manage.py createsuperuser` (e-mail + név + jelszó), majd `/admin/`.
Tesztek: `python manage.py test`.

## Adatbázis

Helyben SQLite (nulla beállítás). Élesben PostgreSQL: állítsd be a `DATABASE_URL` környezeti változót (lásd `.env.example`; az adatbázis neve mindenhol `fixmyhome`).

Helyi PostgreSQL (opcionális): `docker compose up -d db`, majd a `.env`-be: `DATABASE_URL=postgres://fixmyhome:fixmyhome@localhost:5432/fixmyhome`.

## Bemutató adatok

`python manage.py seed_demo` (többször is futtatható). Minden fiók jelszava: `test1234`, ezért **éles vagy alagutas környezetben tilos futtatni**.

- `felhasznalo@fixmyhome.test`: felhasználó (Szabadka), 8 hirdetéssel (nyitott, folyamatban, lezárt; a „Csöpög a konyhai csap” hirdetésre függő jelentkezés vár)
- `villanyszerelo@` (Szabadka; 1 folyamatban lévő és 1 lezárt munka, 1 szolgáltatás), `vizszerelo@` (Palics), `festo@` (Topolya), `asztalos@` (Zenta, nem elérhető): mesterek, mind `@fixmyhome.test`
- `ugyfelszolgalat@fixmyhome.test`: ügyfélszolgálat

## Alagút és éles futtatás

Ha más is eléri az oldalt (Cloudflare-alagút vagy hosting), a `.env`-ben:

```env
DEBUG=0
SECRET_KEY=<véletlen, legalább 50 karakter>   # python -c "import secrets; print(secrets.token_urlsafe(50))"
ALLOWED_HOSTS=<a-te-alagutad>.trycloudflare.com
CSRF_TRUSTED_ORIGINS=https://<a-te-alagutad>.trycloudflare.com
TRUST_PROXY_SSL_HEADER=1
```

- `DEBUG=0` mellett a gyenge kulcs (rövid, `django-insecure`-os vagy a `.env.example`-ben lévő) miatt az oldal **el sem indul**.
- **Proxy/alagút mögött `TRUST_PROXY_SSL_HEADER=1` nélkül végtelen átirányítás lesz:** a Django a proxytól sima HTTP-t lát, és a `SECURE_SSL_REDIRECT` (alapból be) újra és újra HTTPS-re küld. Proxy nélkül viszont **ne** kapcsold be, mert akkor a kliens hamisíthatja az `X-Forwarded-Proto` fejlécet.
- A Cloudflare dokumentációja szerint a proxyzott kéréseknél az `X-Forwarded-Proto` a látogató protokollját tartalmazza ([HTTP headers](https://developers.cloudflare.com/fundamentals/reference/http-headers/)). **Ellenőrizetlen:** a cloudflared/quick tunnel dokumentációja ezt külön nem írja le. Ha a `TRUST_PROXY_SSL_HEADER=1` mellett is végtelen átirányítást kapsz, a fejléc nem érkezik meg; ilyenkor állítsd `SECURE_SSL_REDIRECT=0`-ra (az alagút amúgy is HTTPS).
- `CSRF_TRUSTED_ORIGINS`-be a pontos `https://…` címet írd, ne `*.trycloudflare.com`-ot. A quick tunnel címe minden indításkor új, ezért ilyenkor ezt és az `ALLOWED_HOSTS`-t is frissíteni kell.
- A runserver alapból csak a `127.0.0.1`-en figyel; így kívülről csak az alagúton át érhető el, ezért bízhatunk a proxy fejlécében. Ne indítsd `0.0.0.0`-n.
- HSTS: `SECURE_HSTS_SECONDS` (alapból 3600). Növelni csak akkor, ha az oldal biztosan végig HTTPS marad.

Ellenőrzés indítás előtt: `python manage.py check --deploy`. Csak a `security.W005` és a `security.W021` maradhat (HSTS `includeSubDomains` és `preload`): ezeket szándékosan nem kapcsoljuk be, mert nem a mi kezünkben van a teljes domain.

## Felépítés

- `config/` – Django-beállítások, URL-ek
- `accounts/` – felhasználók, regisztráció, belépés, jogosultságok
- `listings/` – kategóriák, hirdetések, jelentkezések, szolgáltatás-hirdetések
- `templates/` – közös sablonok
- `docs/superpowers/` – terv és megvalósítási terv

## Közös elemek (kinézet)

- A prototípus a `design/`-ban van, a Django ugyanezt a CSS-t használja: `static/css/base.css` (szerkezet és elemek), `static/css/themes/c-brutal.css` (az egyetlen téma: szürke–fekete–lime).
- Oldalváz: minden sablon a `templates/base.html`-ből öröklődik (fejléc, szerepkör szerinti menü, toastok), a tartalom a `{% block content %}`-be kerül: `.page-title` + `.page-lead`, alatta `.card` / `.card-list`.
- Gombok: `.btn` + `.btn-primary` (fő művelet), `.btn-secondary`, `.btn-danger` (törlés, visszavonás). Űrlap: `.form-field` (hibánál `.has-error`), alatta `<p class="field-error">`; a `templates/listings/_form_fields.html` ezt egy sorból kirakja.
- Címkék és jelölők: `.badge` + `.badge-open/-progress/-closed/-withdrawn` (hirdetés), `.badge-pending/-accepted/-rejected` (jelentkezés), `.chip`, `.pill-distance`, `.avatar`, `.toggle`, `.empty-state`, `.toolbar`. Ikonok és avatar: `{% load fmh %}`, `{% icon "pin" %}`, `{% avatar user.name %}`.
- JS-hookok (`static/js/fixmyhome.js`): `[data-geolocate]`, `#map[data-api]`, `input[data-preview]`, `form[data-confirm]`.

## Csapatmunka (git)

- A `main` ág stabil, nem commitolunk rá közvetlenül.
- Minden feladat külön ágon: `feature/<név>-<feladat>` (pl. `feature/kriszti-adatbazis`).
- Kis pull request, a merge squash merge.
- A kód és az azonosítók angolul, a felület magyarul íródik.
- Titkot (`.env`, jelszó, kulcs) soha ne commitolj.
