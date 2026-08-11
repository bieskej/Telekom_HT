# Email audit — HTML predlošci i log

## Predlošci (`backend/app/templates/emails/`)

| Predložak | Kada se šalje | Primatelj |
|-----------|---------------|-----------|
| `dodjela.html` | Nakon uspješne dodjele broja (`dodijeli_broj`) | Email kupca |
| `karantena_start.html` | Pri stavljanju broja u karantenu (`oslobodi_broj`) | Email kupca (ako postoji) |
| `karantena_end.html` | Pri automatskom ili ručnom izlasku iz karantene | Email kupca (ako postoji) |
| `iskoristivost_alert.html` | Kad općina pređe prag iskorištenosti inventara (>= `ISKORISTIVOST_UPOZORENJE_POSTOTAK`, default 90%) | `ADMIN_ALERT_EMAIL` |
| `digest_admin.html` | Tjedni cron (ponedjeljak 08:00 UTC) | `ADMIN_ALERT_EMAIL` |

Svi predlošci nasljeđuju `base.html` (HT plava `#0054A6`, responsive inline CSS).

## Slanje

- Funkcija: `send_html_email()` u `app/services/email_service.py`
- Format: `multipart/mixed` → `multipart/alternative` (text fallback strip tagova + HTML)
- PDF privitak: samo kod dodjele (ugovor)
- Svaki poziv upisuje red u tablicu `email_log`

## Tablica `email_log`

| Stupac | Tip | Opis |
|--------|-----|------|
| `id` | SERIAL | PK |
| `msisdn_id` | INT NULL | FK na `msisdn` |
| `primatelj` | VARCHAR(255) | Email adresa |
| `predmet` | VARCHAR(500) | Subject |
| `status` | VARCHAR(20) | vidi enum ispod |
| `error_text` | TEXT NULL | Poruka greške |
| `html_tijelo` | TEXT NULL | Renderirani HTML za resend |
| `sent_at` | TIMESTAMPTZ NULL | Vrijeme uspješnog slanja |

### Status enum

| Vrijednost | Značenje |
|------------|----------|
| `poslano` | SMTP uspješno |
| `greska` | SMTP ili mrežna greška |
| `nedostaje_smtp` | `SMTP_HOST` / kredencijali nisu postavljeni |

## Admin API

- `GET /admin/email-log?limit=&offset=&status=&msisdn_id=`
- `GET /admin/email-log/{id}/html` — HTML za preview
- `POST /admin/email-resend/{id}` — ponavlja slanje iz `html_tijelo` (bez PDF-a)
- `POST /admin/iskoristivost/provjeri` — ručno okidanje provjere zauzetosti po općinama (>= prag); šalje `iskoristivost_alert.html` adminu i vraća listu općina u JSON-u (samo admin)

## Demo seed + obavijest

Nakon postavljanja demo zauzetosti (npr. Crnići 91%):

```bash
cd backend
python -m scripts.seed_demo_iskoristivost --notify
```

`--notify` poziva istu logiku kao cron (`provjeri_iskoristivost_alert`). U devu poruku pregledaj u smtp4dev Web UI (`http://localhost:5000`).

## Scheduler (cron)

| Job | Raspored | Opis |
|-----|----------|------|
| `_job_digest_admin` | **Ponedjeljak 08:00 UTC** | `digest_admin.html` na admin email |
| Karantena cleanup | Dnevno (postojeći) | + `karantena_end.html` pri izlasku |
| Iskorištenost | **Dnevno 08:00** (Europe/Sarajevo) | `iskoristivost_alert.html` — općine >= 90% |

Konfiguracija: `app/scheduler.py` (APScheduler).

## smtp4dev Desktop (dev — preporučeno)

Lokalni SMTP bez kvote i bez stvarnog slanja primateljima.

1. Instaliraj i pokreni [smtp4dev Desktop](https://github.com/rnwood/smtp4dev/releases) (SMTP obično na **portu 25**).
2. U `backend/.env`:

```env
SMTP_HOST=127.0.0.1
SMTP_PORT=25
SMTP_USER=dev
SMTP_PASSWORD=dev
SMTP_FROM=noreply@eronet.ba
SMTP_USE_TLS=false
ADMIN_ALERT_EMAIL=admin@eronet.ba
```

`SMTP_USER` / `SMTP_PASSWORD` su placeholderi — `smtp_configured()` zahtijeva oba; smtp4dev auth ne provjerava. Mailbox se ne kreira.

3. Restart backend-a (uvicorn).
4. Test: `POST /test-email` ili dodjela broja s emailom kupca.
5. Poruke pregledaj u smtp4dev **Web UI** (npr. `http://localhost:5000`).

## Mailtrap Sandbox (dev — alternativa)

U `.env` postavite Mailtrap SMTP (bez stvarnih lozinki u repou):

```env
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=<mailtrap_user>
SMTP_PASSWORD=<mailtrap_password>
SMTP_FROM=noreply@eronet.ba
SMTP_USE_TLS=true
ADMIN_ALERT_EMAIL=admin@eronet.ba
```

Poruke se ne šalju stvarnim primateljima — pregled u [Mailtrap Sandbox inbox](https://mailtrap.io/).

## Produkcija: Outlook / Gmail

1. Zamijenite SMTP varijable u `.env` (ili tajne u vaultu):
   - **Microsoft 365:** `SMTP_HOST=smtp.office365.com`, port `587`, TLS `true`, korisnik = mailbox.
   - **Gmail (App password):** `SMTP_HOST=smtp.gmail.com`, port `587`, TLS `true`.
2. Postavite `SMTP_FROM` na verificiranu domenu (npr. `noreply@eronet.ba`).
3. Uklonite Mailtrap kredencijale iz produkcijskog okruženja.
4. Provjerite SPF/DKIM za domenu pošiljatelja.
5. Test: `POST /test-email` ili dodjela broja s emailom kupca.

## Frontend

- `/admin/email-log` — tablica logova, filter statusa, HTML preview (iframe), ponovno slanje.
- Dodjela / Brojevi — gumb **Pošalji ugovor ponovno** (zadnji log za `msisdn_id`).
