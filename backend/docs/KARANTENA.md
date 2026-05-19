# Dvosmjerna karantena

## Lifecycle

1. **Zauzet → karantena** — `POST /oslobodi/{id}` (prodaja/admin), postavlja `datum_karantene`, `karantena_dana`, opcionalno kasnije `karantena_razlog`.
2. **Produženje** — `PATCH /msisdn/{id}/karantena` s `produzi_dana` (1–180), povećava ukupno trajanje.
3. **Skraćivanje** — isti endpoint s `skrati_dana`, **samo admin**.
4. **Automatski izlaz** — dnevni cron (`clear_karantena`) kad istekne rok.
5. **Admin oslobađanje** — `POST /msisdn/{id}/oslobodi`, odmah `status=slobodan`, briše podatke kupca, log u `msisdn_history`.

## Privilegije

| Akcija | Prodaja | Admin |
|--------|---------|-------|
| Stavi u karantenu (`POST /oslobodi/{id}`) | ✓ | ✓ |
| Produži karantenu | ✓ | ✓ |
| Skrati karantenu | ✗ | ✓ |
| Oslobodi iz karantene (`POST /msisdn/{id}/oslobodi`) | ✗ | ✓ |

## Polja

| Stupac | Opis |
|--------|------|
| `datum_karantene` | Početak karantene (UTC) |
| `karantena_dana` | Trajanje u danima |
| `karantena_razlog` | Slobodan tekst (max 255) |

Datum isteka = `datum_karantene + karantena_dana`.

## Frontend

- Klik na red u `/brojevi` → modal detalja s sekcijom Karantena.
- Filter status **Karantena** + admin → inline gumb **Oslobodi** u tablici.
