# HT Eronet – sustav dodjele telefonskih brojeva

Demo aplikacija za automatsku dodjelu fiksnih telefonskih brojeva HT Eroneta
(BiH). Backend FastAPI + PostgreSQL + Alembic, frontend React 19 + Vite +
Tailwind + Radix UI + Leaflet.

## Brzi start

```powershell
# Backend (port 8004)
.\scripts\start-backend.ps1

# Frontend (port 5173)
cd frontend
npm run dev
```

Prijava (demo): `admin@eronet.ba` / `admin`.

## Dokumentacija

| Tema | Opis |
|------|------|
| [RAK_IMPORT.md](backend/docs/RAK_IMPORT.md) | Import RAK Excel, formula `sn_len`, plan centrala HT Eroneta |
| [MAPA_OPCINA.md](backend/docs/MAPA_OPCINA.md) | Choropleth mapa općina – GeoJSON endpoint, lat/lon seed |
| [HIJERARHIJA_UI.md](backend/docs/HIJERARHIJA_UI.md) | Master-detail prikaz `/hijerarhija`, sidebar slide-over paneli (Lokacije, MSAN) |
| [KUPAC_PORTAL.md](backend/docs/KUPAC_PORTAL.md) | Portal za kupce — registracija, moji brojevi, ugovor PDF |
| [EMAIL_AUDIT.md](backend/docs/EMAIL_AUDIT.md) | HTML email predlošci, `email_log`, Mailtrap / produkcijski SMTP |
| [KARANTENA.md](backend/docs/KARANTENA.md) | Dvosmjerna karantena, admin oslobađanje |
| [PORTABILNOST.md](backend/docs/PORTABILNOST.md) | Port-in/out tok i statusi |
| [SERVISNI_NALOZI.md](backend/docs/SERVISNI_NALOZI.md) | Kritični nalozi, `u_kvaru` blokada |
| [AUDIT_LOG.md](backend/docs/AUDIT_LOG.md) | Audit trag akcija, CSV export |
| [UI_STIL.md](frontend/docs/UI_STIL.md) | Dark mode, animacije, print |

## Funkcionalnosti (v3.0)

1. **Kupac portal** — `/portal` (registracija, moji brojevi, ugovor PDF)
2. **Port-in / port-out** — `/portabilnost`
3. **Servisni nalozi** — `/servisni-nalozi` (Kanban, HTML5 drag&drop)
4. **Audit log** — `/admin/audit-log` (filteri, CSV)
5. **Email log** — `/admin/email-log` (Mailtrap Sandbox u dev-u)
6. **Dvosmjerna karantena** — produži/skrati/oslobodi
7. **Magični broj** — wildcard `*7777` na `/brojevi`
8. **Dark mode** — toggle u headeru (persist localStorage)
9. **QR na ugovoru** — link na portal kupca
10. **Heatmap dodjela** — dashboard 24×7

Demo seed: `.\scripts\demo-seed.ps1`

## Portal za kupce

Samoposlužni portal na **[http://localhost:5173/portal/prijava](http://localhost:5173/portal/prijava)**:

- Registracija i prijava (uloga `kupac` u tablici `radnici`)
- Pregled brojeva povezanih s JMBG-om
- Preuzimanje ugovora (PDF)
- Kontakt forma za podršku

Radnici se i dalje prijavljuju na `/prijava`.

## Demo emailovi

U razvoju koristite **Mailtrap Sandbox** inbox — HTML emailovi (dodjela s PDF ugovorom, karantena, admin digest) ne idu na stvarne adrese. Konfiguracija u `backend/.env.example`; detalji u [EMAIL_AUDIT.md](backend/docs/EMAIL_AUDIT.md). Admin pregled: `/admin/email-log`.

## Pokretanje migracija i seed-a

```powershell
cd backend
.\.venv\Scripts\Activate.ps1

alembic upgrade head
python -m scripts.seed_inventar_fiksni --ukupno 600000   # ~604 000 MSISDN-a
python -m scripts.seed_opcine_geo                         # lat/lon za 39 općina
```

## Testovi

```powershell
cd backend
python -m pytest --ignore=tests/test_email_service.py
```

Trenutno: **162 passed, 1 skipped**.

## Arhitektura

- **Hijerarhija**: Entitet (FBiH/RS/Brčko) → Županija → Općina → Lokacija
  → Uređaj (MSAN) → Raspon → MSISDN.
- **NDC plan**: 36 HNŽ, 33 KS, 35 TK, 32 ZDŽ, 51 RS-BL, 49 BRC, 37 USŽ,
  38 BPŽ, 39 ZHŽ, 30 SBŽ, 31 ŽP, 34 HBŽ.
- **Kvaliteta MSISDN-a** određena se uzorkom **zadnje 4 znamenke**
  (`silver` ~85 %, `gold` ~10 %, `platinum` ~3 %, `diamond` ~1 %).
- **Karantena** default 60 dana s automatskim cron izlaskom.
- **Županijski fallback** pri dodjeli: ako u zadanoj općini nema slobodnog
  broja, traži se u pool-u iste županije (osim BRC i RS-BL).
