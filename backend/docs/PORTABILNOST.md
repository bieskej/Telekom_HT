# Port-in / Port-out

## Statusi

`zahtjev` → `u_obradi` → `realiziran` | `odbijen`

## Tipovi

- **port_in** — broj dolazi u HT mrežu; polje `broj` obavezno pri kreiranju.
- **port_out** — broj napušta HT; polje `msisdn_id` obavezno.

## Realizacija

- **port_in**: kreira `msisdn` (status `zauzet`) ako broj ne postoji.
- **port_out**: postavlja `msisdn.status = portano`.

## API

- `GET /portabilnost`
- `POST /portabilnost`
- `PATCH /portabilnost/{id}`

## Napomena (RAK BiH)

Portabilnost u produkciji mora biti usklađena s RAK pravilima i međuoperaterskim ugovorima.
