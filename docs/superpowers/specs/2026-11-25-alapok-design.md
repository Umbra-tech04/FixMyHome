# MesterKereső – 1. sprint alapok (Kriszti feladatai) – rövid terv

Dátum: 2026-11-25 · Készítette: Kriszti (Fazekas Krisztián) + Claude

## Miért és mi a cél
A MesterKereső 1. sprintjének alapjait építjük meg: projekt, adatbázis, regisztráció, bejelentkezés (összesen 19 óra a Trello "Kriszti TODO" oszlopban). Mindenki más (Filip, Sasa, Norbi, Adrian) erre épít, ezért a cél: **stabil, egyszerű alap, amin öten, Claude-dal dolgozva, egymás kódjába nyúlás nélkül tudnak haladni.**

## Célok
- Működő közös projekt, amit bárki 5 parancsból elindít.
- Adatmodell, ami lefedi az 1. sprint story-jait (US-16, US-9, US-7, US-1, US-10).
- Regisztráció (felhasználó / mester) és bejelentkezés szerepkör-alapú jogosultsággal.

## Nem célok (ma)
- App kinézete, közös elemek (Filip), térkép/távolság (Sasa), hirdetési űrlapok és jelentkezés folyamata (Norbi), moderáció (Adrian).
- Céges és ügyfélszolgálati regisztráció (US-14, 2. sprint), fizetés, képfeltöltés felülete.
- PWA-elemek (manifest, service worker), hosting/élesítés.

## Anti-célok
- Ne legyen olyan döntés, amit a többieknek ki kell kerülniük (pl. saját, szokatlan szerkezet).
- Ne készüljön "kész" vizuális felület, ami Filip dizájnjával ütközik: a sablonok szándékosan csupaszok.

## Megközelítések (Kriszti rám bízta a technikai döntést)
| Opció | Mellette | Ellene |
|---|---|---|
| **Django + PostgreSQL (választva)** | Auth, jelszótitkosítás, szerepkörök, migrációk, admin felület beépítve; egy nyelv; bárki gyorsan beletanul | Frontend interaktivitás kevesebb, mint SPA-nál |
| Next.js + Supabase | Leggyorsabb, kész auth és képtárolás | Mindenkinek JS/TS kell; jogosultságok a Supabase-ben élnek, nehezebb dokumentálni |
| ASP.NET Core (C#) | Erős, ha a csapat C#-os | PWA és hosting nehézkesebb, több kézi beállítás |

## Döntések (mind az én hívásom, nem egyeztetett)
- **Stack:** Python 3.12, Django 5, HTML/CSS sablonok (mobil-first). Függőségek: `requirements.txt` + venv.
- **Adatbázis:** helyben SQLite (nulla beállítás), élesben PostgreSQL; a `DATABASE_URL` környezeti változó választ (`dj-database-url`). Egyedi, csak PostgreSQL-specifikus funkciót nem használunk.
- **Appok:** `accounts` (felhasználók, regisztráció, belépés), `listings` (kategóriák, hirdetések, jelentkezések, szolgáltatás-hirdetések). A `moderation` appot Adrian hozza létre.
- **Egyedi User modell az első migráció előtt** (Django-korlát: utólag nem cserélhető): `accounts.User`, e-mail a belépési azonosító, mezők: név, e-mail, telefon, `role` (USER, MASTER, SUPPORT, COMPANY). Regisztrációnál csak USER vagy MASTER választható; a másik kettőt később kapja meg a rendszer.
- **Modellek (listings/accounts):**
  - `MasterProfile` (user, szakma = Category, működési terület, elérhetőség, opcionális koordináták a távolságszámításhoz)
  - `Category` (szakmák, seedelve: vízszerelő, villanyszerelő, festő, hegesztő, ...)
  - `Ad` (owner, cím, leírás, category, helyszín szöveg + lat/lon nullable, `status`: OPEN → IN_PROGRESS → DONE (Nyitott → Folyamatban → Lezárva), chosen_master nullable, létrehozva)
  - `AdImage` (ad, kép; a képek nem kötelezők)
  - `Application` (ad, master, létrehozva; egyedi: ad+master)
  - `ServiceListing` (master, cím, leírás, category, működési terület, árkategória, aktív/szüneteltetett; a US-7 elfogadási feltételei szerint)
- **Jogosultság:** `role_required` dekorátor/mixin a nézetekhez; a sablonok is a szerepkör alapján mutatnak menüt.
- **Nyelv:** felület magyarul (`LANGUAGE_CODE = "hu"`, `TIME_ZONE = "Europe/Belgrade"`), kód és azonosítók angolul.
- **Git-munkamenet:** `main` stabil; minden task külön ág (`feature/<név>-<task>`), kis PR-ok, squash merge. README magyarul, telepítés 5 lépésben, `.env.example`, `.gitignore`.
- **Tesztek:** Django tesztek a regisztrációra, belépésre, jogosultságra és a modellek szabályaira (egy e-mail = egy fiók, egy mester egyszer jelentkezhet).

## Munkarend és "akkor van kész, ha"
1. **Projekt indítása (4 óra):** közös GitHub-repó, Django-projekt, `accounts` app üres egyedi User modellel (AUTH_USER_MODEL), adatbázis-kapcsolat, README. *Kész, ha:* tiszta klónból 5 parancsra elindul a szerver és a főoldal betölt.
2. **Adatbázis (6 óra):** fenti modellek, migrációk, kategóriák seedje, admin regisztráció. *Kész, ha:* a migrációk lefutnak, adminban létrehozható hirdetés és jelentkezés, a tesztek zöldek.
3. **Regisztráció (5 óra):** űrlap felhasználónak és mesternek (név, e-mail, jelszó, telefon, szerepkör; mesternél szakma, terület, elérhetőség). *Kész, ha:* egy e-mailhez egy fiók; a jelszó titkosítva tárolódik; rossz adatnál érthető magyar hibaüzenet.
4. **Bejelentkezés (4 óra):** belépés, kilépés, jogosultságok. *Kész, ha:* mindenki csak a szerepköre funkcióit éri el, belépés nélkül védett oldalak a belépéshez irányítanak.

Sorrend: 1 → 2 → 3 → 4 (a 3. és 4. egymásra is épül).

## A kivitelezőre marad
- Pontos mezőhosszok, űrlap-elrendezés, hibaüzenetek szövege, a seedelt kategóriák teljes listája.
- A kártyák leírását (Trello "Akkor van kész, ha") ellenőrizni kell, mielőtt valamelyik DONE-ba megy: a fenti kritériumok a prezentáció alapján íródtak.

## Nyitott kérdés Krisztinek
- Létezik már a közös GitHub-repó, vagy mi hozzuk létre? Kinek a fiókja alatt?
