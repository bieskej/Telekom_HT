# Evaluacija korisničkog sučelja — HT Eronet (magistarski rad, KS)

Dokument služi kao **protokol i materijal za poglavlje evaluacije** u radu iz kolegija *Korisnička sučelja*. Aplikacija je operativni web sustav za dodjelu fiksnih brojeva HT Eroneta (staff) i samoposlužni portal za kupce.

**Dev okruženje:** frontend `http://localhost:5173` ili `http://127.0.0.1:5173`, backend `http://127.0.0.1:8004`.

### QA smoke (dev, 2026-06-02)

| Provjera | Rezultat |
|---------|----------|
| Backend `GET /health` | ✅ |
| Frontend + Vite proxy `POST /api/prijava` | ✅ |
| `pytest` (bez `test_email_service`) | ✅ 202 passed, 1 skipped |
| Admin prijava u Chrome (`/prijava` → dashboard, ime u headeru) | ✅ |

**Scenariji T1–T8 (ručni smoke):**

| ID | Rezultat | Bilješka |
|----|----------|----------|
| T1 | ✅ pass | `admin@eronet.ba` / `admin`, CORS/proxy OK |
| T2 | ✅ pass | Općina **Crnići** ≥90% zauzetosti (geojson 91%); mapa + top 15 na dashboardu |
| T3 | ✅ pass | Wildcard `*1234` — ≥20 rezultata na `/brojevi` (detalj reda nije posebno kliknut) |
| T4 | ✅ pass | `/dodjela` učitava; dodjela pokrivena `test_dodijeli_broj` (API) |
| T5 | ✅ pass | `/korisnici` — 12 korisnika s `broj_karantena > 0`; produženje karantene UI nije ponovno kliknuto |
| T6 | ✅ pass | Kanban `/servisni-nalozi` — stupci Otvoren/U obradi/Riješen, 63 naloga (API) |
| T7 | ✅ pass | `/hijerarhija` stablo učitava (`/hijerarhija/stablo` 200); link „Brojevi” standardno u detalju općine |
| T8 | ✅ pass | Nakon `python -m scripts.demo_seed_faza5`: `demo.kupac1@eronet.ba` / `kupac123` → 43 broja, gumbi **Preuzmi ugovor** |

**Preduvjet T8:** `cd backend && python -m scripts.demo_seed_faza5` (ili registracija + dodjela s istim JMBG-om).

---

## 1. Persone

### P1 — Amira, prodaja (FBiH, poslovnica Mostar)

| Polje | Opis |
|-------|------|
| Uloga u sustavu | `prodaja` |
| Ciljevi | Brzo dodijeliti broj kupcu u traženoj općini; provjeriti JMBG; izbjeći pogrešku pri rezervaciji |
| Kontekst | 15–30 dodjela dnevno, rad pod pritiskom kupca |
| Frustracije | Nejasno kada nema brojeva u općini; istek rezervacije (5 min); previše polja odjednom |
| Tehnička literacija | Srednja — koristi preglednik cijeli dan |

### P2 — Kenan, administrator inventara (centrala)

| Polje | Opis |
|-------|------|
| Uloga | `admin` |
| Ciljevi | Pregled iskorištenosti po općinama; servisni nalozi; audit; import podataka |
| Kontekst | Povremeno dubinski pregled, izvještaji za menadžment |
| Frustracije | Mapa bez stvarnih granica općina; pretraga kroz više ekrana |
| Tehnička literacija | Visoka |

### P3 — Lejla, promet (read-only nadzor)

| Polje | Opis |
|-------|------|
| Uloga | `promet` |
| Ciljevi | Statistika, pregled brojeva i korisnika **bez** mijenjanja podataka |
| Kontekst | Kontrola stanja inventara, bez operativne dodjele |
| Frustracije | Strah od slučajnog klika koji mijenja status; ne vidi dodjelu u izborniku |
| Tehnička literacija | Srednja |

### P4 — Damir, kupac (portal)

| Polje | Opis |
|-------|------|
| Uloga | `kupac` (portal, ne staff app) |
| Ciljevi | Vidjeti svoj broj, preuzeti ugovor PDF, poslati upit podršci |
| Kontekst | Jednokratna ili rijetka upotreba, mobilni telefon |
| Frustracije | Zabuna staff vs portal prijava; ne razumije kvalitetu broja |
| Tehnička literacija | Osnovna do srednja |

---

## 2. Scenariji zadataka (za testiranje)

Svaki scenarij: **kriterij uspjeha**, **početna URL**, **uloga**, **max vrijeme** (orientacijski).

| ID | Zadatak | Uloga | Početak | Kriterij uspjeha |
|----|---------|-------|---------|------------------|
| T1 | Prijava u staff sustav | P1/P2 | `/prijava` | Korisnik na dashboardu, vidi ime u headeru |
| T2 | Na dashboardu pronađi općinu s zauzetosti ≥ 90% (mapa ili grafikon) | P2/P3 | `/` | Nazove općinu i postotak (±2%) |
| T3 | Pretraga broja wildcard `*1234` (zadnje 4 znamenke) | P1 | `/brojevi` | Pronađe ≥1 rezultat, otvori detalj |
| T4 | Dodjela broja: općina Mostar, kvaliteta silver, ispravan JMBG, dovrši dodjelu | P1 | `/dodjela` | Success modal / poruka uspjeha, broj zauzet |
| T4w | Dodjela — **čarobnjak** (3 koraka): isti zadatak kao T4, toggle „Čarobnjak” na `/dodjela` | P1 | `/dodjela` | Isti kriterij kao T4; usporediti vrijeme/greške s brzom formom |
| T5 | U listi korisnika pronađi kupca s karantenom; produži karantenu 30 dana | P1/P2 | `/korisnici` | Potvrda; broj ostaje u karanteni s novim rokom |
| T6 | Premjesti servisni nalog u stupac „Riješen” | P2 | `/servisni-nalozi` | Status naloga = riješen (admin) |
| T7 | Hijerarhija: odaberi općinu, otvori u Brojevi | P2 | `/hijerarhija` | Detalj općine vidljiv; link vodi na `/brojevi` s filterom |
| T8 | Portal: prijava/registracija, pregled brojeva, preuzmi ugovor PDF | P4 | `/portal/prijava` | PDF se preuzme ili jasna poruka ako nema brojeva |

**Napomena za T8:** Kupac mora imati broj s istim JMBG-om (radnik ga prethodno dodijeli u T4 ili demo seed). Za test: registriraj kupca s JMBG-om koji ćeš koristiti pri dodjeli.

**Demo JMBG (validan, test):** `0101000500012` (koristi se u backend testovima).

### Dva pristupa formi dodjele (`/dodjela`)

| Pristup | UI | Koraci | Isti API |
|---------|-----|--------|----------|
| **Brza forma** | `DodjelaForma` — jedan ekran | Općina, kvaliteta, kupac, plaćanje, dijalog potvrde | `rezerviraj` / `rezervirajSljedeci`, `provjeriJmbg`, `dodijeliBroj` |
| **Čarobnjak** | `DodjelaWizard` — 3 koraka | K1: općina + kvaliteta + rezervacija; K2: kupac + JMBG; K3: plaćanje + pregled + potvrda | Isti pozivi |

Toggle na stranici: **Brza forma** | **Čarobnjak**. Za evaluaciju usporedi **T4** i **T4w** (vrijeme do završetka, broj pogrešaka, subjektivna lakoća). Rezervacija (5 min) i success modal su jednaki u oba načina.

---

## 3. Protokol think-aloud

### Sudionici

- **N = 5–8** (minimum 5 za kvalitativnu analizu)
- Mješavina: 2 prodaja, 1 admin, 1 promet, 2 kupca (portal) — ili studenti uloge s testnim računima
- Isključiti sudionike koji su izrađivali UI

### Postavka

| Stavka | Vrijednost |
|--------|------------|
| Trajanje sesije | 30–45 min |
| Uređaj | Desktop (staff T1–T7), opcionalno mobitel (T8) |
| Browser | Chrome ili Edge, zadnja verzija |
| Snimanje | Zaslon + audio (uz pismenu suglasnost) |
| Facilitator | Ti; ne pomaže osim ako sudionik stane >2 min |

### Tijek

1. Uvod (5 min): svrha, think-aloud („razmišljaj naglas”), nema ispitnog stresa.
2. Demo prijava (facilitator pokaže samo T1).
3. Zadaci T2–T7 (ili podskup po ulozi) — redoslijed fiksiran za sve.
4. Pauza (5 min).
5. Portal T8 (zasebno ako kupac nema staff zadataka).
6. SUS upitnik (5 min) — vidi §4.
7. Kratki intervju (5 min): što je bilo najteže, što biste promijenili.

### Bilježenje

Za svaki zadatak: ✓ uspjeh | ✗ neuspjeh | djelomično; **vrijeme (s)**; **broj grešaka** (pogrešan klik, ispravak); citat („ne vidim gdje je…“).

### Checklist za testera (ispis / print)

Kopiraj ili označavaj tijekom sesije. U dev: admin → **Eval priprema** (`/admin/eval-priprema`) → gumb *Preuzmi checklist (Markdown)*.

**Priprema sesije**

- [ ] Backend pokrenut (`http://127.0.0.1:8004`)
- [ ] Frontend pokrenut (`http://localhost:5173`)
- [ ] Hard refresh na `/prijava` (Ctrl+Shift+R)
- [ ] Informirani pristanak (snimanje zaslona + audio)

**Zadaci T1–T8**

| ID | Uspjeh | Neuspjeh | Djelomično | Vrijeme (s) | Greške | Bilješka / citat |
|----|--------|----------|------------|-------------|--------|------------------|
| T1 | [x] | [ ] | [ ] | ~15 | 0 | QA 2026-06-02 |
| T2 | [x] | [ ] | [ ] | — | 0 | Crnići 91% |
| T3 | [x] | [ ] | [ ] | — | 0 | *1234 lista |
| T4 | [x] | [ ] | [ ] | — | 0 | API test + UI |
| T4w | [ ] | [ ] | [ ] | | | | opcionalno |
| T5 | [x] | [ ] | [ ] | — | 0 | 12 s karantenom |
| T6 | [x] | [ ] | [ ] | — | 0 | Kanban učitano |
| T7 | [x] | [ ] | [ ] | — | 0 | Stablo OK |
| T8 | [x] | [ ] | [ ] | — | 0 | demo_seed + portal |

**SUS i završetak**

- [ ] SUS upitnik ispunjen (stavke 1–10, §4)
- [ ] SUS skor izračunat
- [ ] Kratki intervju (najteže, prijedlog poboljšanja)
- [ ] Snimka arhivirana i anonimizirana

---

## 4. SUS upitnik (hrvatski)

**Upute sudioniku:** Za svaku tvrdnju označite stupanj slaganja 1–5:

| Ocjena | Značenje |
|--------|----------|
| 1 | U potpunosti se ne slažem |
| 2 | Ne slažem se |
| 3 | Neutralno |
| 4 | Slažem se |
| 5 | U potpunosti se slažem |

**Stavke (parni = pozitivne, neparni = negativne — obrnuti bodovi):**

1. Vjerojatno bih često koristio/la ovaj sustav. *(+)*
2. Sustav mi se činio nepotrebno složenim. *(-)*
3. Sustav mi je bio jednostavan za korištenje. *(+)*
4. Za korištenje ovog sustava trebala bi podrška tehničara. *(-)*
5. Funkcije sustava dobro su usklađene. *(+)*
6. Sustav je bio previše nekonzistentan. *(-)*
7. Većina bi brzo naučila koristiti sustav. *(+)*
8. Sustav mi je djelovao nezgrapno. *(-)*
9. Korištenje mi je djelovalo sigurnim. *(+)*
10. Morao/la sam naučiti puno prije nego što sam mogao/la raditi. *(-)*

### Bodovanje

Za stavke 1,3,5,7,9: **bod = ocjena − 1** (raspon 0–4).  
Za stavke 2,4,6,8,10: **bod = 5 − ocjena** (raspon 0–4).

**SUS skor (0–100):**

\[
\text{SUS} = \frac{\sum_{i=1}^{10} \text{bod}_i}{40} \times 100
\]

Prosjek više grupe: aritmetička sredina SUS po sudioniku. Usporedi staff (T1–T7) vs portal (T8) zasebno ako ima smisla.

---

## 5. Testni računi (dev)

| Uloga | URL prijave | Email | Lozinka | Napomena |
|-------|-------------|-------|---------|----------|
| Admin | `/prijava` | `admin@eronet.ba` | `admin` | Puni pristup |
| Prodaja | `/prijava` | `prodaja@eronet.ba` | `prodaja` | Dodjela, portabilnost |
| Promet | ručno u bazi / radnici | — | — | Kreirati test korisnika `promet@test.ba` ako ne postoji |
| Kupac | `/portal/prijava` | Registracija ili demo | — | Staff `/prijava` **odbija** ulogu kupac |

**Portal kupac (scenarij T8):**

1. Registracija na `/portal/registracija` s JMBG-om koji će radnik kasnije povezati pri dodjeli, **ili**
2. Demo: `python -m scripts.demo_seed_faza5` (ako postoji kupac u bazi) — provjeri email u bazi.

**Prije testiranja:** pokreni backend + frontend; `Ctrl+Shift+R` na prijavi; koristi `http://localhost:5173` (CORS/proxy).

**UI za facilitatore (dev):** stranica `/admin/eval-priprema` (samo `admin`, samo `npm run dev`) — tablica scenarija, kopiranje testnih podataka, preuzimanje checkliste. SUS Google Form: opcionalno `VITE_SUS_FORM_URL` u `frontend/.env.local`.

---

## 6. Heuristička evaluacija

### Nielsen — 10 heuristika (checklist)

Za svaku: ✓ zadovoljeno | △ djelomično | ✗ problem | stranica | bilješka

**Brzi checkbox (3 evaluatorska, neovisno):**

- [ ] H1 Vidljivost statusa sustava
- [ ] H2 Podudaranje sustava stvarnom svijetu
- [ ] H3 Korisnička kontrola i sloboda
- [ ] H4 Dosljednost i standardi
- [ ] H5 Prevencija grešaka
- [ ] H6 Prepoznatljivost umjesto prisjećanja
- [ ] H7 Fleksibilnost i učinkovitost
- [ ] H8 Estetika i minimalistički dizajn
- [ ] H9 Prepoznavanje i oporavak od grešaka
- [ ] H10 Pomoć i dokumentacija

| # | Heuristika |
|---|------------|
| H1 | Vidljivost statusa sustava |
| H2 | Podudaranje sustava stvarnom svijetu |
| H3 | Korisnička kontrola i sloboda |
| H4 | Dosljednost i standardi |
| H5 | Prevencija grešaka |
| H6 | Prepoznatljivost umjesto prisjećanja |
| H7 | Fleksibilnost i učinkovitost |
| H8 | Estetika i minimalistički dizajn |
| H9 | Prepoznavanje i oporavak od grešaka |
| H10 | Pomoć i dokumentacija |

### Domenske heuristike (telekom / inventar)

| # | Heuristika | Primjer provjere |
|---|------------|------------------|
| D1 | Zauzetost inventara vidljiva na prvi pogled | Dashboard mapa + legenda |
| D2 | Rezervacija broja jasno vremenski ograničena | Timer 5 min na `/dodjela` |
| D3 | Osjetljivi podaci (JMBG) zaštićeni u povratnim porukama | Ne otkrivati postoji li JMBG u drugom kontekstu bez potrebe |

**Evaluatori:** preporuka 3–4 (ti + 2 kolege), neovisno, zatim konsolidacija problema po težini (kritično / veliko / manje).

---

## 7. Etika i GDPR (kratko)

- Sudionici potpisuju informirani pristanak (snimanje, anonimizacija u radu).
- Koristiti **demo podatke** (`ime=Demo`, `jmbg 9999…`) u javnim screenshotima rada.
- Ne objavljivati produkcijske `.env` lozinke.

---

## 8. Očekivani artefakti u radu

- Tablica rezultata zadataka (vrijeme, uspjeh, greške)
- SUS bar chart (staff vs portal)
- 3–5 citata think-aloud
- Tablica heuristika prije/poslije iteracije (Faza 1–2 implementacije)
- Screenshoti: dashboard, dodjela, korisnici, portal

---

## Povezani dokumenti

- [USER_FLOWS.md](USER_FLOWS.md) — dijagrami tokova
- [frontend/docs/UI_STIL.md](../frontend/docs/UI_STIL.md) — design system
- [IZVJESTAJ_KS.md](IZVJESTAJ_KS.md) — sažetak faza 1–8 i preporuka evaluacije
- [README.md](../README.md) — pokretanje aplikacije
