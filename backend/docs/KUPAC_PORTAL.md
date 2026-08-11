# Portal za kupce

Samoposlužni portal na `/portal/*` za pregled dodijeljenih MSISDN brojeva,
preuzimanje ugovora (PDF) i slanje upita podršci.

## Model korisnika

Kupac **nije zasebna tablica** — koristi `radnici` s `uloga = 'kupac'`:

| Polje | Namjena |
|-------|---------|
| email | Prijava |
| lozinka_hash | Prijava |
| jmbg | Povezivanje s `msisdn.jmbg` |
| ime, prezime | Prikaz u portalu |

Obrazloženje: isti mehanizam JWT + bcrypt kao radnici; razlikuje se samo uloga
i pristupnim rutama.

## API endpointi

| Metoda | Ruta | Auth | Opis |
|--------|------|------|------|
| POST | `/kupac/registracija` | Ne | Nova registracija (JMBG validacija) |
| POST | `/kupac/prijava` | Ne | JWT token (samo uloga kupac) |
| GET | `/kupac/moji-brojevi` | Kupac | Paginacija 20/stranica |
| GET | `/kupac/ugovor/{msisdn_id}` | Kupac | PDF download |
| POST | `/kupac/kontakt` | Kupac | Poruka u `kupac_kontakt` |

## Matrica privilegija

| Ruta / akcija | admin | prodaja | promet | kupac |
|---------------|:-----:|:-------:|:------:|:-----:|
| `/admin/*` | OK | 403* | 403* | **403** |
| `/radnici` | OK | 403 | 403 | **403** |
| `/dodijeli-*`, `/dodjela` | OK | OK | 403 | **403** |
| `/kupac/*` | **403** | **403** | **403** | OK |
| `/statistike`, `/brojevi` | OK | OK | OK | **403** |
| `/portal/*` (frontend) | — | — | — | OK |

\* Ovisi o konkretnoj ruti; prodaja nema admin ovlasti.

Implementacija:

- **Middleware** (`AuthMiddleware`): token s `uloga=kupac` → 403 na
  `/admin*`, `/radnici*`, `/dodijeli*`, te na sve ostalo osim `/kupac/*` i
  javnih ruta.
- **RequireKupac** dependency: samo `uloga=kupac` na `/kupac/moji-brojevi`,
  `/kupac/ugovor`, `/kupac/kontakt`.
- **Staff `/prijava`**: odbija `uloga=kupac` (preusmjerava na portal).

## Tok registracije i prijave

```
1. Kupac → /portal/registracija
2. POST /kupac/registracija {ime, prezime, email, jmbg, lozinka}
   - 400 ako JMBG ne prolazi modul 11
   - 409 ako email već postoji
3. Automatska prijava → POST /kupac/prijava
4. Redirect → /portal/moji-brojevi
5. GET /kupac/moji-brojevi → MSISDN gdje msisdn.jmbg = radnici.jmbg
```

## Demo: otvoriti broj kupcu za testiranje

1. Pokreni migraciju: `alembic upgrade head`
2. Registriraj kupca na `/portal/registracija` (zapamti JMBG).
3. Prijavi se kao **admin** na `/prijava`.
4. Idi na **Dodjela** → dodijeli broj u općini s **istim JMBG-om** kao kupac.
5. Kupac se odjavi/prijavi na portalu → **Moji brojevi** prikazuje broj.
6. **Preuzmi ugovor** generira PDF preko `contract_pdf.py`.

Alternativa (bez portala): admin na `/radnici` kreira korisnika s ulogom
`kupac` + JMBG, zatim dodjela s istim JMBG-om.

## Frontend

- **Zasebni auth**: `portalAuthStorage` + `PortalAuthContext` (ne dijeli token
  s radničkom aplikacijom).
- **Layout**: `PortalLayout` — header s logom i Odjava, bez admin sidebara.
- **Rute**: `/portal/prijava`, `/portal/registracija`, `/portal/moji-brojevi`,
  `/portal/kontakt`.

## Migracija

```powershell
cd backend
alembic upgrade head
```

Dodaje `radnici.jmbg`, tablicu `kupac_kontakt`, proširuje CHECK na ulogu
(`kupac`).

## Testovi

```powershell
pytest tests/test_kupac_auth.py tests/test_kupac_moji_brojevi.py tests/test_kupac_ugovor.py -q
```
