# RAK import – formula `sn_len`, geografska raspodjela i fiksni inventar

## Sažetak (2026-05-19v2 – fiksna telefonija 604 k)

- **Format MSISDN**: 8 znamenki = **NDC(2) + CENTRALA(3) + PRETPLATNIK(3)**.
  Primjer: `36 853 474` (Stolac), `36 325 720` (Mostar), `33 261 234` (Sarajevo).
- **Plan centrala** (`app/services/centrale_plan.py`) – stvarne HT Eronet
  centrale iz javnih izvora (Stolac 850-869, Mostar 200-499, Čapljina 800-839,
  Konjic 700-749 itd.). Garantirane centrale (`GARANTIRANE_CENTRALE`) osiguravaju
  pokrivenost realnih HT brojeva i u skaliranim demo seedovima.
- **Inventar 600 k**: `seed_inventar_fiksni.py --ukupno 600000` → **604 000**
  novih slobodnih MSISDN-a (zauzeti i karantena ostaju netaknuti).
- **Kvaliteta po zadnje 4 znamenke** (`kvaliteta_klasifikacija.py`) –
  pooštrena pravila: diamond 1.1 %, platinum 2.7 %, gold 10.5 %, silver 85.7 %.
- **Stara formula `sn_len`** (`raspon_granice`) i dalje vrijedi za RAK Excel
  import; novi format `centrala-3` plan upotrebljava se za demo/seed.

## Formula `raspon_granice`

| Primjer | NDC | Blok | Dužina | len(prefiks) | sn_len | Brojeva/red |
|---------|-----|------|--------|--------------|--------|-------------|
| 30-3049 | 30  | 3049 | 8      | 6            | 2      | 100         |
| 36-3612 | 36  | 3612 | 9      | 6            | 3      | 1 000       |
| 64-440  | 64  | 440  | 9      | 5            | **4**  | **10 000**  |

E.164 limit: `Dužina ≤ 9` (N(S)N max 9 znamenki). Ako `sn_len ≤ 0` red se preskoči s logom.

## Geografska raspodjela (`rak_geografija.py`)

Prioritet:
1. Stupac `Općina` iz Excela (ako postoji).
2. `data/rak_ndc_opcina_map.csv` (ručne iznimke NDC+Blok).
3. `NDC_OPCINA_FALLBACK` (čvorovi).
4. Raspodjela na sve općine županije iz `data/opcine_master.csv` (round-robin).

NDC fallback:
```
30 Travnik  (SBŽ)        37 Bihać     (USŽ)
31 Orašje   (ŽP)         38 Goražde   (BPŽ)
32 Zenica   (ZDŽ)        39 Š. Brijeg (ZHŽ)
33 Sarajevo (KS)         49 Brčko     (BRC)  ← bez raspodjele
34 Livno    (HBŽ)        51 Banja Luka(RS-BL) ← bez raspodjele
35 Tuzla    (TK)         63 Mostar    (HNŽ)
36 Mostar   (HNŽ)        64 Mostar    (HNŽ)
```

## Fiksni inventar (`scripts/seed_inventar_fiksni.py`) – preporučeno

Generira ~600 k brojeva po **stvarnim HT centralama**.

```
python -m scripts.seed_inventar_fiksni --dry-run --ukupno 600000
python -m scripts.seed_inventar_fiksni --ukupno 600000
python -m scripts.seed_inventar_fiksni --ukupno 600000 --force-karantena
```

NDC po županiji (RAK plan numeriranja BiH):

```
30 SBŽ   31 ŽP    32 ZDŽ   33 KS    34 HBŽ   35 TK
36 HNŽ   37 USŽ   38 BPŽ   39 ZHŽ   49 BRC   51 RS-BL
```

### Klasifikacija kvalitete (zadnja 4 znamenke)

| Tier      | Pravilo                                                     | Primjer       |
|-----------|-------------------------------------------------------------|---------------|
| diamond   | sve 4 iste / 1234 / 4321 / palindrom 4 (1221, 7337)         | `36207777`    |
| platinum  | XYYY ili YYYX (3+1) / ABAB (1212, 7373)                     | `36202111`    |
| gold      | zadnje 2 iste a prethodna različita (XYY) / monotone 3      | `36854432`    |
| silver    | ostalo (default, ~85 %)                                     | `36325720`    |

## Populacijski seed (`scripts/seed_inventar.py`) – legacy

Cilj: realniji demo. Mostar > Stolac > Neum prema stvarnoj populaciji.

```
python -m scripts.seed_inventar --ukupno 150000 --force-karantena
python -m scripts.seed_inventar --dry-run --ukupno 200000
```

Format MSISDN-a: 9 znamenki = NDC(2) + SLOT(3) + SN(4). Slot per općina iznosi
10 000 brojeva; veće općine dobivaju više slotova.

NDC po županiji za seed:
```
HNŽ→63   ZHŽ→39   HBŽ→34   KS→33   TK→35   ZDŽ→32   SBŽ→30
BPŽ→38   USŽ→37   ŽP→31    BRC→49  RS-BL→51
```

## CHANGELOG 2026-05-19v2 (fiksna telefonija, 604 k)

- **Ukupno MSISDN**: 604 000 slobodnih + 11 zauzetih + 7 ostalih = **604 018**
- **Po NDC-u**: 36 (HNŽ) 129 000, 33 (KS) 128 000, 35 (TK) 51 000, 32 (ZDŽ) 38 000,
  51 (RS-BL) 64 000, 49 (BRC) 23 000, 37 (USŽ) 20 000, …

### Top općine

| # | Općina       | NDC | Centrala          | MSISDN |
|---|--------------|-----|-------------------|-------:|
| 1 | Sarajevo     | 33  | 200-327           |128 000 |
| 2 | Mostar       | 36  | 200-496 (77 cent.)| 77 000 |
| 3 | Banja Luka   | 51  | 200-263           | 64 000 |
| 4 | Tuzla        | 35  | 200-250           | 51 000 |
| 5 | Zenica       | 32  | 200-237           | 38 000 |
| 6 | Brčko        | 49  | 200-222           | 23 000 |
| 7 | Bihać        | 37  | 200-219           | 20 000 |
| 8 | Konjic       | 36  | 700-712           | 13 000 |
| 9 | Travnik      | 30  | 500-512           | 13 000 |
|10 | Goražde      | 38  | 200-212           | 13 000 |
|11 | Čitluk       | 36  | 640-649           | 10 000 |
|12 | **Čapljina** | 36  | 800-809           | 10 000 |
|13 | Bugojno      | 30  | 250-259           | 10 000 |
|14 | **Stolac**   | 36  | 850-854           |  5 000 |
|15 | Jablanica    | 36  | 750-754           |  5 000 |
|16 | Prozor       | 36  | 770-774           |  5 000 |
|17 | Neum         | 36  | 880               |  1 000 |
|18 | Ravno        | 36  | 890               |  1 000 |

### Verificirani stvarni HT brojevi u bazi

| Broj         | Općina   | Kvaliteta |
|--------------|----------|-----------|
| `36 325 720` | Mostar   | silver    |
| `36 336 821` | Mostar   | silver    |
| `36 395 000` | Mostar   | platinum  |
| `36 853 474` | Stolac   | silver    |
| `36 853 101` | Stolac   | silver    |
| `36 854 432` | Stolac   | gold      |
| `36 805 052` | Čapljina | silver    |
| `36 805 060` | Čapljina | silver    |
| `36 805 681` | Čapljina | silver    |
| `36 729 813` | Konjic   | silver    |
| `36 735 370` | Konjic   | silver    |
| `36 880 094` | Neum     | silver    |

### Distribucija kvalitete

| Tier     | Brojeva | Postotak |
|----------|--------:|---------:|
| silver   | 517 628 |  85.70 % |
| gold     |  63 178 |  10.46 % |
| platinum |  16 308 |   2.70 % |
| diamond  |   6 886 |   1.14 % |

### Promjene u kodu (v2)

- `backend/app/services/centrale_plan.py` (novi) – plan HT centrala s
  garantiranim centralama za realne primjere.
- `backend/app/services/kvaliteta_klasifikacija.py` – nova pravila po
  zadnje 4 znamenke.
- `backend/scripts/seed_inventar_fiksni.py` (novi) – generator 600 k brojeva
  iz `centrale_plan`, automatska reklasifikacija kvaliteta.
- `backend/tests/test_centrale_plan.py` (novi) – 13 testova (Stolac 36853474,
  Mostar 36325720, Čapljina 36805052 … moraju biti unutar plana).
- `backend/tests/test_kvaliteta_klasifikacija.py` – prepisani testovi za
  nova pooštrena pravila (38 testova).
- `backend/tests/test_import_rak.py` – testne blokove prebaceni izvan plana
  centrala (9991-9993) jer 888x sada zauzima Hodovo/Crnići.

## CHANGELOG (2026-05-19v1 – populacijski seed)

- **Ukupno MSISDN**: 150 033 slobodnih + 11 zauzetih + 0 karantena = **150 044**
- **Po entitetu**:
  - FBiH: **123 068**
  - RS:    **18 614** (samo Banja Luka – ostali RS gradovi izvan prioriteta)
  - Brčko: **8 351**

### Top 25 općina

| # | Općina           | Županija | Entitet | MSISDN |
|---|------------------|----------|---------|-------:|
| 1 | Sarajevo         | KS       | FBiH    | 27 670 |
| 2 | Banja Luka       | RS-BL    | RS      | 18 614 |
| 3 | Zenica           | ZDŽ      | FBiH    | 11 169 |
| 4 | Tuzla            | TK       | FBiH    | 11 169 |
| 5 | Mostar           | HNŽ      | FBiH    | 10 576 |
| 6 | Brčko            | BRC      | Brčko   |  8 351 |
| 7 | Bihać            | USŽ      | FBiH    |  5 635 |
| 8 | Travnik          | SBŽ      | FBiH    |  5 333 |
| 9 | Livno            | HBŽ      | FBiH    |  3 421 |
|10 | Tomislavgrad     | HBŽ      | FBiH    |  3 220 |
|11 | Bugojno          | SBŽ      | FBiH    |  3 119 |
|12 | Široki Brijeg    | ZHŽ      | FBiH    |  2 918 |
|13 | Ljubuški         | ZHŽ      | FBiH    |  2 817 |
|14 | Jajce            | SBŽ      | FBiH    |  2 717 |
|15 | Vitez            | SBŽ      | FBiH    |  2 616 |
|16 | Konjic           | HNŽ      | FBiH    |  2 515 |
|17 | Goražde          | BPŽ      | FBiH    |  2 515 |
|18 | **Čapljina**     | HNŽ      | FBiH    |  2 415 |
|19 | Novi Travnik     | SBŽ      | FBiH    |  2 314 |
|20 | Kiseljak         | SBŽ      | FBiH    |  2 214 |
|21 | Posušje          | ZHŽ      | FBiH    |  2 113 |
|22 | Odžak            | ŽP       | FBiH    |  1 912 |
|23 | Orašje           | ŽP       | FBiH    |  1 912 |
|24 | Čitluk           | HNŽ      | FBiH    |  1 811 |
|25 | **Stolac**       | HNŽ      | FBiH    |  1 409 |

### Manje HNŽ općine (sve > 0)

| Općina | MSISDN |
|--------|-------:|
| Prozor    | 1 409 |
| Jablanica |   906 |
| Neum      |   503 |
| Ravno     |   302 |
| Crnići    |   101 |
| Hodovo    |   100 |

### Promjene u kodu

- `backend/app/services/rak_import.py` – nova `raspon_granice` formula (sn_len),
  raspodjela po općinama iz `rak_geografija`.
- `backend/app/services/rak_geografija.py` (novi) – pravila raspodjele i
  `osiguraj_opcinu` koja relocira općine ako su u krivoj županiji.
- `backend/app/services/populacija.py` (novi) – populacijske kvote.
- `backend/scripts/seed_inventar.py` (novi) – generira 150 k MSISDN-a.
- `backend/scripts/migrate_raspon_10k.py` (novi) – reimport iz baze po novoj formuli.
- `backend/app/services/msisdn_service.py` – `_find_slobodan_ids` + `_zakljucaj_rezervirani_msisdn`
  imaju **fallback po županiji** (npr. korisnik u Stocu može dobiti broj iz HNŽ poola).
- `frontend/src/components/dodjela/{DodjelaForma,BulkDodjelaModal}.tsx` – `api.opcine()`
  bez `samo_s_brojevima`; sve općine vidljive operatoru.

### Testovi (`backend/tests`)

- `test_rak_raspon_granice.py` – primjeri 100, 1 000, 10 000.
- `test_rak_geografija.py` – HNŽ pool, NDC 49/51 bez raspodjele.
- `test_dodjela_zupanijski_pool.py` – Stolac/Čapljina imaju slobodne, fallback HNŽ.
- `test_pretraga_opcina.py` – endpoint `/opcine` i `/msisdn/pretraga`.

Pokretanje: `cd backend && python -m pytest --ignore=tests/test_email_service.py`.

### Statusi MSISDN-a (proširenje v3.0)

| Status | Značenje |
|--------|----------|
| `slobodan` | Dostupan za rezervaciju/dodjelu (`u_kvaru=false`) |
| `zauzet` | Dodijeljen kupcu |
| `karantena` | Čeka istek roka prije ponovne dodjele |
| `portano` | Port-out realiziran — broj napustio HT mrežu |

**`u_kvaru`**: kada je na MSAN-u otvoren **kritičan** servisni nalog, svi brojevi tog uređaja imaju `u_kvaru=true` i ne ulaze u `_find_slobodan_ids` ni wildcard pretragu.

### Sigurnost

- `migrate_raspon_10k.py` i `seed_inventar.py` ne brišu **zauzete** MSISDN-e.
- `--force-karantena` mora biti eksplicitno postavljeno za brisanje karantene.
- Nikad TRUNCATE na produkciji.
- `.env`, lozinke nisu u repo-u; git config se ne mijenja iz skripti.
