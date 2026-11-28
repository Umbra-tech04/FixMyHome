# FixMyHome

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

### Adatbázis-szabályok

A fontos szabályokat az adatbázis is kikényszeríti (`accounts/0006_db_constraints`, `listings/0004_db_constraints`), nem csak a Python kód. Így a `queryset.update()`, a `bulk_create()`, a shell, a nyers SQL vagy egy import sem vihet be rossz adatot (`IntegrityError` jön). Az admin és a modellűrlapok ugyanezt magyar hibaüzenettel mutatják (`violation_error_message`).

- **E-mail:** kis- és nagybetűtől függetlenül egyedi (`UniqueConstraint(Lower("email"))`, a `unique=True` mellett), és nem lehet üres.
- **Értékkészlet:** `User.role`, `Ad.status`, `ServiceListing.price_category` csak a kódban felsorolt értékek egyike lehet. Új érték felvételekor a `makemigrations` új migrációt készít a szabályhoz; a `makemigrations --check` jelzi, ha ez elmaradt.
- **Koordináták** (`Ad`, `MasterProfile`): szélesség -90..90, hosszúság -180..180, és vagy mindkettő meg van adva, vagy egyik sem.
- **Hirdetés:** a gazdája nem lehet a kiválasztott mester.
- **Üres szöveg:** az `Ad` és a `ServiceListing` címe, valamint a `Category` neve nem lehet üres (`""`). A csak szóközből álló szöveget az adatbázis nem tiltja; az űrlapok levágják a szóközöket.
- **Index:** `Ad(category, status)` a mester kezdőoldalának lekérdezéséhez (`listings.geo.nearby_open_ads`: nyitott hirdetések a szakmájában). Más index nem került be: a többi lekérdezést a meglévő indexek kiszolgálják (idegen kulcsok, egyedi megszorítások).
- **Szándékosan nincs szabály** az `Ad.status` és az `Ad.chosen_master` kapcsolatára (pl. „folyamatban lévőnek kell mester”), és az `on_delete` sem változott: a mester fiókjának törlése (`SET_NULL`) a folyamatban lévő munkáin nullázza a `chosen_master`-t. A szerepkör- és törlési szabályok csapatdöntések (5. PR).

**Migráláskor:** a migráció előbb ellenőrzi a meglévő adatokat. Ha valamelyik sor sérti az új szabályokat (pl. két fiók e-mail-címe csak kis/nagybetűben különbözik), érthető hibaüzenettel megáll, felsorolja a sorokat, és **semmit nem változtat** (nem töröl, nem egyesít). Ilyenkor kézzel (pl. az adminban) kell javítani, majd újra futtatni a `python manage.py migrate`-et. A migráció visszafordítható (`migrate accounts 0005`, `migrate listings 0003`). A `seed_demo` adatai megfelelnek a szabályoknak.

**Ismert korlátok:**

- SQLite-on a `lower()` csak az ASCII betűket alakítja kisbetűssé, ezért ott az ékezetes nagybetűket (pl. egy `Á`-t a domainben) az adatbázis-szabály nem veszi észre. A `User.save()` és a PostgreSQL igen.
- A bejelentkezés és a regisztráció `email__iexact`-tel keres, ami PostgreSQL-en `UPPER(email)`. Ezt a kisbetűs index nem gyorsítja. A javítás (kisbetűs, pontos egyezéssel keresni) külön feladat.
- Az admin a kis/nagybetűs duplikált e-mailre két hibát mutat: egy általánosat (az új szabályé) és egy mezőhibát (a `unique=True`-é).
- Ha valaki a hirdetés vagy a mesterprofil rejtett koordinátamezőjét kézzel tartományon kívüli értékre írja, az űrlap két hibát mutat (a település mezőn és általános hibaként). A rendes böngészős használatban ez nem fordul elő.

### PostgreSQL-próba (nincs ellenőrizve)

A szabályok és a migrációk csak hordozható eszközöket használnak (`Lower`, `Q`, `F`, sima `Index`), de **PostgreSQL-en még senki nem futtatta őket**: a fejlesztő gépén nem volt sem PostgreSQL, sem Docker. Aki tudja, futtassa le így (Docker kell hozzá):

```bash
docker run --rm -d --name fixmyhome-pg -e POSTGRES_DB=fixmyhome -e POSTGRES_USER=fixmyhome \
  -e POSTGRES_PASSWORD=fixmyhome -p 5432:5432 postgres:16
export DATABASE_URL=postgres://fixmyhome:fixmyhome@localhost:5432/fixmyhome   # PowerShell: $env:DATABASE_URL="postgres://..."
python manage.py migrate && python manage.py seed_demo && python manage.py test --shuffle
docker stop fixmyhome-pg   # a --rm miatt a konténer és az adatai törlődnek
```

Ha már fut egy PostgreSQL, elég a `DATABASE_URL`-t beállítani. A tesztekhez a felhasználónak adatbázist kell tudnia létrehozni (`test_fixmyhome`). Az SQLite-specifikus indexteszt PostgreSQL-en kimarad (skip).

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

## Regisztráció: adatellenőrzés

A szabályok az `accounts/validators.py`-ban vannak; a regisztrációs űrlap és az admin (a `User` modell mezői) is ezeket használja.

- **E-mail:** levágott szóközök, kisbetű, max. 254 karakter; a domainben kell pont (a `valaki@localhost` és az IP-címes domain nem megy át). Eldobható címek tiltva a [`disposable-email-domains`](https://github.com/disposable-email-domains/disposable-email-domains) csomag listája és az `EXTRA_DISPOSABLE_DOMAINS` saját lista alapján (aldomainekkel együtt). Új domaint az utóbbiba lehet felvenni.
- **Telefon:** a `phonenumbers` csomag ellenőrzi; alapértelmezett régió Szerbia (`RS`), nemzetközi előhívóval bármely ország. Csak érvényes szám megy át, és E.164 alakban (`+381641234567`) mentjük. A régi adatokat nem írjuk át: az adminban egy régi formátumú számot mentéskor javítani kell, ilyenkor E.164-re alakul.
- **Név:** 2–150 karakter, betűk (ékezetekkel is), szóköz, kötőjel, aposztróf és pont; a többszörös szóközöket összevonjuk.
- **Jelszó:** nem lehet túl hasonló az e-mail-címhez, a névhez vagy a telefonszámhoz.

## Jelszótippelés elleni védelem

A `/belepes/` és az `/admin/` belépést a [django-axes](https://django-axes.readthedocs.io/) védi:

- 5 hibás próba után az adott e-mail-cím 15 percre tiltva van, még helyes jelszóval is. Sikeres belépés nullázza a számlálót.
- A tiltás **e-mail-cím szerint** történik, kis- és nagybetűtől függetlenül (`Anna@x.hu` = `anna@x.hu`). Nem IP szerint, mert alagút mögött minden kérés a `127.0.0.1`-ről jön. Ezért kapcsoltuk ki az `axes.W006` figyelmeztetést.
- Az IP-t (csak naplózáshoz) a `REMOTE_ADDR`-ből veszi; a hamisítható `X-Forwarded-For` fejlécet nem használja.
- Ismeretlen e-mail-címre ugyanúgy számol és ugyanazt a tiltási oldalt mutatja (HTTP 429), így nem derül ki, létezik-e a fiók.
- Hátrány: ha valaki ismeri egy felhasználó e-mail-címét, 5 rossz jelszóval 15 percre kizárhatja.
- Sikeres belépést nem naplózunk; az adminban (Axes → Access attempts) csak a sikertelen próbák látszanak, és ott törölhetők is.

Beállítások (`.env`): `AXES_FAILURE_LIMIT` (alapból 5), `AXES_COOLOFF_MINUTES` (alapból 15). Mindkettő legalább 1 értékű egész szám; hibás értéknél az oldal nem indul el.

Kézi feloldás:

```bash
python manage.py axes_reset_username anna@example.com   # egy fiók feloldása (kisbetűvel)
python manage.py axes_reset                             # minden tiltás és próbálkozás törlése
```

## E-mail-megerősítés

Regisztráció után **nincs automatikus belépés**: a felhasználó az „Elküldtük a levelet” oldalra kerül, és levelet kap egy 24 óráig érvényes megerősítő linkkel. Amíg nem kattint rá, helyes jelszóval sem léphet be (sem a `/belepes/`, sem az `/admin/` oldalon); a hibaüzenetben van link az újraküldéshez (`/email-megerosites/ujrakuldes/`).

- **Fejlesztésben** (`EMAIL_BACKEND=console`, ez az alapérték) a levél nem megy ki, hanem a `runserver` terminálja írja ki; a linket onnan lehet kimásolni. **Élesben** `EMAIL_BACKEND=smtp` kell az SMTP-beállításokkal (lásd `.env.example`); a jelszó (`EMAIL_HOST_PASSWORD`) csak a `.env`-be kerülhet. A console backend élesben a szerver naplójába írná a megerősítő linkeket.
  - Windows: ha a kimenet nem UTF-8 (pl. átirányítod fájlba, vagy IDE-ből futtatod), az ékezetes levelet a terminál nem tudja kiírni; ilyenkor a levél elmarad, és a naplóban `UnicodeEncodeError` jelenik meg. Megoldás: `set PYTHONUTF8=1` (PowerShell: `$env:PYTHONUTF8=1`) a `runserver` előtt.
  - A teszteket (`python manage.py test`) viszont **`PYTHONUTF8` nélkül** futtasd: a `config/tests.py` beállítás-tesztjei tiszta környezetű gyerekfolyamatot indítanak, amely a rendszer kódolásával (cp1252) ír, a `PYTHONUTF8=1`-es szülő pedig UTF-8-ként olvasná, ezért `UnicodeDecodeError`-ral elbuknak.
- A levelek szövege: `templates/accounts/email/` (sima szöveg, magyarul). Az oldal nevét (tárgy, aláírás) a `SITE_NAME` beállítás adja (alapból `FixMyHome`, a `.env`-ben felülírható). A feladó a `DEFAULT_FROM_EMAIL`, alapból `<SITE_NAME> <noreply@localhost>` (pl. `FixMyHome <noreply@localhost>`); élesben a `.env`-ben a valódi címre kell állítani.
- **Meglévő fiókok:** az `email_verified` mező alapértéke `True`, ezért a régi fiókok, a `seed_demo`, a `createsuperuser` és az adminban létrehozott fiókok megerősítettek. Csak a regisztrációs űrlap ad `False`-t.
- **Mesterek:** a regisztrált mester profilja `is_available=False`-szal jön létre, így nem látszik a keresésben (`listings/geo.py`), amíg meg nem erősíti a címét; a megerősítés `True`-ra állítja.
- **Admin:** a felhasználók listájában szűrhető az „e-mail megerősítve” mező, és a „Kijelöltek e-mail-címének megerősítése” művelettel kézzel is megerősíthető (ez a mester profilját is láthatóvá teszi). A szerkesztőoldalon a pipa átállítása ezt **nem** teszi; ott a profil „most elérhető” mezőjét külön kell állítani.

### Biztonság

- **A token:** a `django.core.signing` írja alá a `SECRET_KEY`-jel, saját salttal (`accounts.email-verification`), adatbázis-tábla nélkül. A tartalma a felhasználó azonosítója és az e-mail-cím kulcsolt hash-e (HMAC-SHA256 a `SECRET_KEY`-jel és saját salttal, a kisbetűs, szóközök nélküli címből), ezért címváltozásnál érvénytelen lesz. A hamisított, lejárt vagy más felhasználóhoz tartozó tokenre hibaoldal jön. Az újrafelhasználás ártalmatlan: a már megerősített fiókon nem változtat semmit. A `SECRET_KEY` cseréje minden kiküldött linket érvénytelenít.
- **A link nem léptet be**, csak megerősít, majd a belépési oldalra irányít (így a token a címsorból is eltűnik). Ha egy levélszűrő előre megnyitja a linket, az is megerősíti a címet. Ez csak annyit bizonyít, hogy a levél megérkezett a postafiókba, ezért elfogadjuk.
- **Host-fejléc:** a link abszolút címét a `request.build_absolute_uri` adja a kérés `Host` fejlécéből. Az `ALLOWED_HOSTS` véd: idegen hostra 400 jön, és nem megy ki levél. Ezért kell az `ALLOWED_HOSTS`-ba a **pontos** cím: egy `*` vagy `.trycloudflare.com` mellett egy támadó a saját domainjére mutató linket küldethetne valaki más postafiókjába.
- **Naplók:** a token benne van az URL-ben, ezért a webszerver hozzáférési naplójában (a `runserver` terminálban is) látszik. Csak 24 óráig érvényes, és csak megerősíteni lehet vele, belépni nem. A `signing` aláír, de nem titkosít: a token első része base64-es JSON, ezért került bele a cím helyett csak a kulcsolt hash-e. A naplóból így a felhasználó azonosítója olvasható ki, a cím nem, és a `SECRET_KEY` ismerete nélkül egy gyanított címet sem lehet a tokennel összevetni. Saját kódunk sem a tokent, sem a címzettet nem naplózza (levélküldési hibánál csak a hiba típusát és a felhasználó azonosítóját).
- **Belépés és axes:** a megerősítetlen fiók elutasítása a jelszó ellenőrzése *után* történik (`confirm_login_allowed`), ezért az axes nem számolja sikertelen próbának. Rossz jelszónál a szokásos hibaüzenet jön, így az, hogy „van fiók, csak nincs megerősítve”, csak a jelszó ismerőjének derül ki.

### Nem derül ki, van-e fiók egy címhez (K3)

- **Regisztráció:** ha a címhez már van fiók, **ugyanaz** az átirányítás és oldal jön, mint új címnél, hibaüzenet nélkül (a válasz bájtra azonos, erre teszt van). A cím tulajdonosa „Valaki ezzel a címmel próbált regisztrálni” levelet kap (címenként legfeljebb óránként egyet). Ha a meglévő fiók még nincs megerősítve, helyette új megerősítő levelet kap, mert neki a „lépj be” nem segítene. Inaktív fióknak nem megy levél. A párhuzamos regisztráció (`IntegrityError`) is erre az ágra fut.
- **Újraküldés:** a válasz mindig „Ha van ilyen fiók, elküldtük a levelet.”, akkor is, ha nincs ilyen fiók, már meg van erősítve, vagy a korlát miatt nem ment levél.
- **Maradó különbség az időzítésben.** A meglévő-cím ágon is lefut a jelszó hashelése (ez a lassú lépés), így a két ág ideje közel van egymáshoz. Ami marad:
  - az új fióknál van adatbázis-írás (INSERT, mesternél kettő), a meglévőnél nincs;
  - ahol levél megy ki, ott az SMTP-kapcsolat ideje is hozzáadódik; ahol nem (a korlát miatt, inaktív fióknál, vagy újraküldésnél nem létező címre), ott a válasz észrevehetően gyorsabb;
  - teljesen csak az tüntetné el, ha a levelek háttérben (sorból, pl. Celery) mennének ki. Ez nincs megcsinálva.

### Levélkorlátok

| Levél | Korlát (címenként) |
|---|---|
| megerősítő levél (regisztráció és újraküldés együtt) | 1 / perc és 5 / óra |
| „már van fiókod” | 1 / óra |
| jelszó-visszaállító levél (külön számláló) | 1 / perc és 5 / óra |

A számlálók a Django cache-ében vannak (a kulcsban a cím SHA-256 hash-e szerepel, nem maga a cím), és az óra az első levéltől számított fix ablak. Az alapértelmezett `LocMemCache` **folyamatonként külön** számol, és újraindításkor nullázódik: N worker folyamatnál a valódi korlát akár N-szeres. Ezek a korlátok a postafiókok elárasztása ellen védenek, nem biztonsági határok. Pontos korláthoz közös cache kell (`CACHES`: Redis, Memcached vagy `DatabaseCache`). IP szerinti korlát nincs, ezért sok különböző címre egyenként a fenti korlátig lehet levelet küldetni.

### Ismert, elfogadott kockázat: előzetes regisztráció (pre-hijacking)

Ha valaki **más e-mail-címével** regisztrál, a cím tulajdonosa megerősítő levelet kap. Ha a tulajdonos rákattint a linkre, pedig nem ő kérte, a fiók megerősítetté válik, és **a támadó jelszavával** lehet belépni. Ez a kockázat ismert, és elfogadjuk:

- a levél kifejezetten kéri: „Ha nem te regisztráltál, ne kattints a linkre”;
- ezt az elfelejtett jelszó funkció kezeli (lásd lent): a cím tulajdonosa új jelszót állít be, és a támadó jelszava ezzel érvényét veszti. A bejelentkezett felhasználó saját jelszócsere-oldala még nincs kész; addig az admin is tud segíteni (jelszócsere vagy a fiók törlése az adminban);
- a fiókban a tulajdonosnak még nincs saját adata: a nevet és a telefonszámot a támadó adta meg.

## Elfelejtett jelszó

A belépés oldalon (és a tiltás oldalán) az „Elfelejtetted a jelszavad?” link a `/jelszo-visszaallitas/` oldalra visz. Ott az e-mail-cím megadása után **mindig** ugyanaz az „Ha van ilyen fiókod, elküldtük a levelet.” oldal jön (K3), akkor is, ha nincs ilyen fiók, vagy a korlát miatt nem ment levél.

- **Ki kap levelet:** aktív fiók, megerősítetlen is. Inaktív fiók és **superuser nem**: a superuser jelszavát a `python manage.py changepassword <e-mail>` parancs cseréli, így egy feltört postafiókkal nem lehet teljes admin jogot szerezni. A sima staff fiókok (pl. ügyfélszolgálat) a normál visszaállítást használják. Az `/admin/` belépés oldalán ezért nincs „elfelejtett jelszó” link.
- **A link:** a Django `PasswordResetTokenGenerator`-a készíti (`PASSWORD_RESET_TIMEOUT`: 1 óra). A token a felhasználó jelszó-hash-éhez, utolsó belépéséhez és e-mail-címéhez kötött, ezért egyszer használható: a jelszócsere (és egy közbeni belépés is) érvényteleníti. Megnyitáskor a token a munkamenetbe kerül, és az oldal a token nélküli `/jelszo-visszaallitas/<azonosító>/uj-jelszo/` címre irányít (a Django `PasswordResetConfirmView` mintája), így a token nem marad a címsorban és a `Referer` fejlécben.
- **Az új jelszó:** ugyanazok a szabályok, mint a regisztrációnál (nem hasonlíthat a fiók e-mail-címéhez, nevéhez, telefonszámához; legalább 8 karakter, nem gyakori, nem csak szám), és a két mezőnek egyeznie kell.
- **Sikeres csere után:** a fiók **minden meglévő munkamenete kilép** (a Django a munkamenetben a jelszó hash-éből képzett értéket tárol), és az aktuális böngésző is. Nincs automatikus belépés: a belépés oldal jön a „Jelszavad megváltozott” üzenettel. A címre vonatkozó belépési tiltás (axes) törlődik. A megerősítetlen fiók megerősítetté válik (a levél megérkezése bizonyítja, hogy övé a postafiók), és a rejtett mester profilja látható lesz.
- **Levél:** `templates/accounts/email/password_reset_*.txt`; az oldal nevét, mint a többi levélnél, a `SITE_NAME` beállítás adja.
- **Korlátok és időzítés:** címenként 1 / perc és 5 / óra (lásd a fenti táblázatot és a `LocMemCache` megjegyzést). A levél minden ágon elkészül (token, sablon), csak a kiküldés marad el, de ahol levél megy ki, ott az SMTP ideje hozzáadódik: a levél nélküli válasz így is észrevehetően gyorsabb lehet. Teljesen csak a háttérben (sorból) küldött levél tüntetné el.
- **Naplók:** a tokenes első kérés címe a hozzáférési naplóba bekerül (a `runserver` terminálban is látszik); a link 1 óráig érvényes, és csak a következő oldalon beírt új jelszóval használható. Egy levélszűrő, amely előre megnyitja a linket, nem cserél jelszót.

## Felépítés

- `config/` – Django-beállítások, URL-ek
- `accounts/` – felhasználók, regisztráció, e-mail-megerősítés, belépés, elfelejtett jelszó, jogosultságok
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
