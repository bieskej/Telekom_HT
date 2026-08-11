# Hijerarhija UI — master-detail prikaz

Dokument opisuje redizajn stranice `/hijerarhija` i nove desne slide-over
panele u sidebaru (Lokacije, MSAN uređaji).

## 1. Master-detail layout

Stranica `/hijerarhija` u prošloj verziji prikazivala je samo općine i njihove
poštanske urede. Nova verzija je **master-detail**:

```
┌────────────────────────────┬─────────────────────────────────────────┐
│  STABLO (1/3 širine)       │  DETALJ ODABRANOG ČVORA (2/3 širine)    │
│                            │                                         │
│  ▼ HNŽ (HNK)        65 432 │  Mostar                                 │
│    ▼ Mostar         50 100 │  Općina                                 │
│      ▶ HT - Mostar  50 100 │  ┌──────┬─────────┬────────┬──────────┐ │
│    ▼ Stolac          7 200 │  │Ukupno│Slobodni │Zauzeti │Karantena │ │
│      ▶ HT - Stolac   7 200 │  │50 100│ 38 540  │ 11 200 │    360   │ │
│  ▼ Sarajevski kanton …     │  └──────┴─────────┴────────┴──────────┘ │
│  …                         │  Iskoristivost: ████░░░░ 22%            │
│                            │                                         │
│                            │  Uzorak MSISDN brojeva (10)             │
│                            │  036 200 100  slobodan  silver          │
│                            │  …                                      │
│                            │                                         │
│                            │  [ Otvori u Brojevi → ]                 │
└────────────────────────────┴─────────────────────────────────────────┘
```

Stablo prikazuje **četiri razine**: Županija → Općina → Lokacija → MSAN
uređaj. Svaka razina ima badge s ukupnim brojem MSISDN-a u toj grani.

Prazno stanje (kada nije ništa odabrano) pokazuje plavu ikonu i poruku
**„Odaberi čvor s lijeve strane“**.

## 2. URL query format

Odabrani čvor se sprema u URL kao query parametri. Time je stanje
**dijeljivo** (URL se može poslati kolegi) i `back/forward` u browseru radi:

```
/hijerarhija?tip=lokacija&id=5
/hijerarhija?tip=opcina&id=12
/hijerarhija?tip=uredjaj&id=421
/hijerarhija?tip=zupanija&id=3
```

`tip` mora biti jedan od `zupanija | opcina | lokacija | uredjaj`, a `id`
pozitivan cijeli broj. Nevaljani parametri se ignoriraju (prazno stanje).

Klik u stablu poziva `setSearchParams({ tip, id: String(id) })` — što čuva
sve ostale query parametre netaknutim (ne briše ih). Detaljna kartica
dohvaća podatke s `GET /hijerarhija/cvor?tip=<tip>&id=<id>`.

## 3. Expand / collapse stanje

Stanje proširenih grana stabla (`expZ`, `expO`, `expL`) drži se u **React
state-u** u komponenti `HijerarhijaStablo` (`useState<Set<number>>`):

- nije perzistirano (osvježi stranicu → sve grane su zatvorene),
- pretraga **automatski širi sve čvorove** koji odgovaraju upitu,
- kad se promijeni odabrani čvor, sve grane do njega se automatski šire,
- klik na chevron sklapa/širi pojedinu granu bez utjecaja na odabir.

Razlog odluke: stablo nije veliko (cca. 200 čvorova), filtriranje je
trenutno; persistiranje u localStorage bi dodalo komplikaciju bez koristi.

## 4. Backend endpoints

### `GET /hijerarhija/stablo`

Vraća cijelo stablo odjednom (Županija → Općina → Lokacija → Uređaj) sa
zbrojevima MSISDN-a (`ukupno / slobodni / zauzeti / karantena`) na svakoj
razini. Iz odgovora se **izuzimaju prazne grane** (npr. županija bez
ijednog MSISDN-a).

Razina **uređaj** dodatno nosi `uredjaj_tip` (MSAN/OLT…). Veličina odgovora
za 600k MSISDN-a / ~200 uređaja: ~30–50 KB JSON.

```jsonc
[
  {
    "tip": "zupanija",
    "id": 3,
    "naziv": "Mostar",          // koristi se sjediste, fallback oznaka
    "oznaka": "HNŽ",
    "entitet": "FBiH",
    "ukupno": 65432, "slobodni": 50000, "zauzeti": 15000, "karantena": 432,
    "opcine": [ /* … */ ]
  }
]
```

### `GET /hijerarhija/cvor?tip=<tip>&id=<id>`

Detalj jednog čvora:

- `metrike` — ukupno / slobodni / zauzeti / karantena
- `brojevi_uzorak` — do 10 MSISDN-a tog čvora (broj, status, kvaliteta)
- `filter_param` — par `{kljuc, vrijednost}` za izgradnju `/brojevi?…` linka
  (kljuc je npr. `uredjaj_id`, `lokacija_id`, `opcina_naziv`)

Za `tip=zupanija` `filter_param` je `null` jer `/brojevi` nema filter po
županiji (mogla bi se dodati u budućnosti).

## 5. Sidebar slide-over paneli

Stari accordion (`▼ Lokacije` razvija dropdown unutar sidebara) zamijenjen
je s **dvije NavLink stavke** koje otvaraju **desni slide-over panel**
(Radix Dialog, `components/ui/Sheet.tsx`):

- **Lokacije** — stablo Županija → Općina → Lokacija + pretraga. Klik na
  lokaciju vodi na `/brojevi?lokacija_id=<id>` i zatvara panel.
- **MSAN uređaji** — pretraga + lista kartica (naziv, općina, kapacitet).
  Klik vodi na `/brojevi?uredjaj_id=<id>` i zatvara panel.

Panel ima `translate-x-full → translate-x-0` tranziciju (300 ms ease-out),
poluprozirni overlay s blur efektom i zatvara se na `Esc`, klik izvan
panela ili klik na ✕.

Pretraga širi sve čvorove stabla koji odgovaraju upitu.

## 6. Testovi

Backend (`backend/tests/test_hijerarhija_stablo.py`):

- `test_stablo_ima_zupanije_opcine_lokacije_msan` — struktura odgovora
- `test_counts_se_poklapaju_sa_statistikom` — zbrojevi se slažu sa
  `/statistike.ukupno`, kao i hijerarhijski (županija = Σ općina = Σ
  lokacija = Σ uređaja).
- `test_stablo_grane_imaju_msisdn` — prazni čvorovi se ne vraćaju
- `test_cvor_uredjaj_vraca_uzorak_brojeva` — `/cvor` endpoint, do 10
  brojeva s `filter_param`.
- `test_cvor_nepostojeci_404` i `test_cvor_neispravan_tip_422`.
- `test_stablo_zahtjeva_autentifikaciju` — 401/403 bez tokena.

Frontend (Vitest **nije instaliran** u ovom trenutku — vidi
`package.json`). U `SidebarExtras.tsx` ostavljen je TODO komentar za
buduće `Sidebar.test.tsx` koji bi trebao testirati da klik na "Lokacije"
otvara Sheet, te `HijerarhijaPage.test.tsx` koji testira da odabir čvora
ažurira URL query.

## 7. TODO za daljnja proširenja

- Persistencija odabranog čvora i expand stanja u localStorage (opcija
  korisnika u postavkama).
- Drag-to-resize za omjer 1/3 : 2/3.
- Tipkovnička navigacija (↑/↓ kroz stablo, Enter otvara detalj).
- Filter po statusu MSISDN-a u uzorku (Slobodno/Zauzeto/Karantena).
