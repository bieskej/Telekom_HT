# Audit log

## Akcije

| Akcija | Entitet | Kada |
|--------|---------|------|
| `prijava` | radnik | Uspješna prijava |
| `dodjela` | msisdn | Dodjela broja |
| `oslobodeno_iz_karantene` | msisdn | Admin oslobađanje |
| `port_port_in_realizacija` | portabilnost | Realizacija port-in |
| `port_port_out_realizacija` | portabilnost | Realizacija port-out |
| `servisni_nalog_otvoren` | servisni_nalog | Novi nalog |
| `servisni_nalog_zatvoren` | servisni_nalog | Zatvaranje naloga |

## `detalji_json`

JSON objekt s kontekstom (email, broj, msisdn_id, prioritet…).

## API

- `GET /admin/audit-log?radnik_id=&entitet=&od=&do=&q=&limit=100`
- `GET /admin/audit-log/export.csv`
