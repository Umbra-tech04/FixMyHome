# MesterKereső (FixMyHome)

Progresszív webalkalmazás, amely összeköti a műszaki problémára megoldást keresőket a közelben elérhető mesterekkel. Iskolai csapatprojekt (VTŠ), Python 3.12 + Django 5.

## Indítás 5 lépésben

```bash
git clone https://github.com/Umbra-tech04/FixMyHome.git && cd FixMyHome   # 1. klónozás
python3.12 -m venv .venv && source .venv/bin/activate                     # 2. venv (Windows: .venv\Scripts\activate)
pip install -r requirements.txt                                           # 3. függőségek
cp .env.example .env && python manage.py migrate                          # 4. beállítás + adatbázis
python manage.py runserver                                                # 5. indítás: http://127.0.0.1:8000
```

Admin felülethez: `python manage.py createsuperuser` (e-mail + név + jelszó), majd `/admin/`.
Tesztek: `python manage.py test`.

## Adatbázis

Helyben SQLite (nulla beállítás). Élesben PostgreSQL: állítsd be a `DATABASE_URL` környezeti változót (lásd `.env.example`).

Helyi PostgreSQL (opcionális): `docker compose up -d db`, majd a `.env`-be: `DATABASE_URL=postgres://fixmyhome:fixmyhome@localhost:5432/fixmyhome`.

## Bemutató adatok

`python manage.py seed_demo` (többször is futtatható). Minden fiók jelszava: `test1234`.

- `felhasznalo@fixmyhome.test`: felhasználó (Szabadka), 3 nyitott hirdetéssel
- `villanyszerelo@` (Szabadka), `vizszerelo@` (Palics), `festo@` (Topolya), `asztalos@` (Zenta, nem elérhető): mesterek, mind `@fixmyhome.test`
- `ugyfelszolgalat@fixmyhome.test`: ügyfélszolgálat

## Felépítés

- `config/` – Django-beállítások, URL-ek
- `accounts/` – felhasználók, regisztráció, belépés, jogosultságok
- `listings/` – kategóriák, hirdetések, jelentkezések, szolgáltatás-hirdetések
- `templates/` – közös sablonok
- `docs/superpowers/` – terv és megvalósítási terv

## Közös elemek (kinézet)

- A prototípus a `design/`-ban van, a Django ugyanezt a CSS-t használja: `static/css/base.css` (szerkezet és elemek), `static/css/themes/*.css` (4 színtéma, a fejlécben váltható).
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
