# Servisni nalozi

## Prioriteti

`niski` | `srednji` | `kritican`

## Statusi

`otvoren` → `u_obradi` → `rijesen`

## Automatska MSAN blokada

Kad je nalog `status=otvoren` i `prioritet=kritican`, svi MSISDN-ovi na tom uređaju dobivaju `u_kvaru=true`.  
`_find_slobodan_ids` i wildcard pretraga preskaču brojeve s `u_kvaru=true`.

Zatvaranje naloga (`rijesen`) ponovno evaluira ima li još kritičnih otvorenih naloga na uređaju.

## API

- `GET /servisni-nalozi`
- `POST /servisni-nalozi`
- `PATCH /servisni-nalozi/{id}`
