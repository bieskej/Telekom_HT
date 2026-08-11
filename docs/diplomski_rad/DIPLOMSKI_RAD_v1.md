# Diplomski / završni rad — v1 (radni nacrt)

**Format:** prema FOI uzorku (Baranašić, 2024) — naslovnica, izjava, sažetak, sadržaj, poglavlja.  
**Autor:** Boško Raguž  
**Institucija prakse:** HT d.d. Mostar (projekt H104515959)  
**Fakultet:** FSRE, Sveučilište u Mostaru (prilagoditi studij/mentora)

> Ovo je **prva verzija** teksta za daljnju doradu, proširenje i PDF. Literatura: vidi `LITERATURA_PRETRAGA.md`.

---

## NASLOVNICA (predložak)

```
SVEUČILIŠTE U MOSTARU
FAKULTET STROJARSTVA, RAČUNARSTVA I ELEKTROTEHNIKE

Boško Raguž

RAZVOJ WEB SUSTAVA ZA UPRAVLJANJE INVENTAROM
I AUTOMATSKU DODJELU FIKSNIH TELEFONSKIH BROJEVA

[DIPLOMSKI RAD / ZAVRŠNI RAD]

Mentor: [ime mentora FSRE]
Mentor u praksi: Zlatko Raguž, dipl. ing. el.

Mostar, 2026.
```

---

## IZJAVA O IZVORNOSTI

Izjavljujem da je moj diplomski/završni rad izvorni rezultat mog rada te da se u izradi istoga nisam koristio drugim izvorima osim onima koji su u njemu navedeni.

Boško Raguž

---

## SAŽETAK

Cilj rada je opisati analizu, projektiranje i implementaciju web sustava za upravljanje inventarom fiksnih telefonskih brojeva i automatiziranu dodjelu korisnicima govorne usluge u nepokretnoj mreži. Sustav je razvijen u okviru stručne prakse u HT d.d. Mostar kao demo modul inspiriran poslovnim procesima HT Eronet mreže.

Implementirana je tro-slojna arhitektura: React 19 klijentska aplikacija, FastAPI REST poslužitelj i PostgreSQL baza podataka s približno 600 000 MSISDN zapisa. Ključne funkcionalnosti uključuju hijerarhijski inventar (općina → lokacija → uređaj → raspon → broj), pretragu i rezervaciju broja na pet minuta, dodjelu uz validaciju JMBG-a (modul 11), klasifikaciju kvalitete broja, mehanizam karantene, županijski fallback te samoposlužni portal kupca za pregled dodijeljenih brojeva i preuzimanje ugovora u PDF formatu.

Rad obuhvaća definiciju funkcionalnih i nefunkcionalnih zahtjeva, opis korištenih tehnologija, projektiranje baze i API-ja, pregled implementacije te rezultate testiranja (automatski pytest i ručni scenariji). Zaključuje se da sustav u obliku prototipa uspješno pokriva tok od pretrage slobodnog broja do dodjele kupcu, uz jasno naznačena ograničenja demo okruženja.

**Ključne riječi:** web aplikacija; telefonska numeracija; MSISDN; FastAPI; React; PostgreSQL; rezervacija; dodjela brojeva; telekomunikacije

---

## ABSTRACT

*(Opcionalno — engleski sažetak za FSRE predložak)*

This thesis describes the design and implementation of a web system for managing fixed telephone number inventory and automated assignment to voice service customers in a fixed network. The system uses a three-tier architecture with React, FastAPI, and PostgreSQL. Key features include hierarchical inventory, five-minute number reservation, customer assignment with JMBG validation, number quality tiers, quarantine, county-level fallback, and a customer self-service portal. The work presents requirements, architecture, implementation, and testing results of a functional demo prototype.

**Keywords:** web application; telephone numbering; MSISDN; FastAPI; React; PostgreSQL; reservation; number assignment

---

## SADRŽAJ

1. Uvod  
2. Analiza predmeta i pregled literature  
3. Opis projektnog zadatka i zahtjevi  
4. Korištene tehnologije i alati  
5. Projektiranje sustava  
6. Implementacija  
7. Testiranje i rezultati  
8. Zaključak  
9. Literatura  
Prilog A — Pregled API endpointa za dodjelu  

---

## 1. UVOD

### 1.1. Motivacija

U telekomunikacijskom operatora dodjela fiksnog broja kupcu tradicionalno uključuje provjeru inventara po lokaciji, izbjegavanje dvostruke dodjele istog broja te usklađivanje podataka o pretplatniku. Ručni ili neintegrirani procesi usporavaju aktivaciju usluge i povećavaju rizik od pogrešaka. Projekt u HT d.d. Mostar (broj H104515959) postavljen je s ciljem razvoja centraliziranog programa za dodjeljivanje numeracija korisnicima govorne usluge u nepokretnoj mreži.

### 1.2. Cilj i opseg rada

Cilj rada je dokumentirati i evaluirati web sustav koji:

- vodi inventar MSISDN brojeva po administrativnoj i mrežnoj hijerarhiji;
- omogućuje prodajnom osoblju rezervaciju i dodjelu broja;
- validira identitet kupca (JMBG);
- generira ugovor u PDF formatu;
- nudi kupcu portal za pregled dodijeljenih brojeva.

Opseg rada **ne** obuhvaća produkcijsku integraciju s komercijalnim BSS/OSS operatora niti službene katastarske granice općina na karti.

### 1.3. Struktura rada

Poglavlje 2 daje pregled srodnih radova. Poglavlje 3 opisuje projektni zadatak iz prakse. Poglavlja 4–6 obrađuju tehnologije, dizajn i implementaciju. Poglavlje 7 prikazuje testiranje. Poglavlje 8 donosi zaključak.

---

## 2. ANALIZA PREDMETA I PREGLED LITERATURE

Pretraga repozitorija FER, ZIR, FOI, ETFOS, DABAR i međunarodnih baza (vidi `LITERATURA_PRETRAGA.md`) **nije identificirala** diplomski rad s identičnom temom (fiksna numeracija + web + rezervacija + hijerarhija MSAN/OLT).

Najbliži radovi:

| Rad | Relevantnost |
|-----|--------------|
| Kapec (FER, 2025) — rezervacija termina, React, PostgreSQL, JWT | Metodologija rezervacije i uloga |
| BSS integration / NMS modul (Theseus) | Životni ciklus MSISDN (reserve/assign) |
| Globethesis — fixed-line newly installed business | Poslovni tok odabira broja |
| Maršić (FER, 2023) — telekom narudžbe | Domen operatora |
| felipevcc/telephone-system (GitHub) | Funkcionalna paralela dodjele po području |

Teorijski okvir: MSISDN kao javni identifikator pretplatnika (Čičić, 2020); BSS/OSS podjela poslovne i mrežne podrške; E.164 format broja u BiH (NDC + centra + pretplatnički broj).

---

## 3. OPIS PROJEKTNOG ZADATKA I ZAHTJEVI

### 3.1. Projektni zadatak (HT Mostar)

- **Naziv:** Izrada programa za dodjeljivanje numeracija korisnicima govorne usluge u nepokretnoj mreži  
- **Broj:** H104515959  
- **Razdoblje:** 12. 04. 2026. – 19. 06. 2026. (360 h)  
- **Voditelj:** Zlatko Raguž; **nalogodavac:** Damir Zelenika  
- **Faze:** inicijacija, dizajn, razvoj, testiranje  

### 3.2. Funkcionalni zahtjevi (izvedeni)

| ID | Zahtjev |
|----|---------|
| F1 | Autentifikacija radnika (uloge admin, prodaja, promet) |
| F2 | Pregled inventara i zauzetosti po općinama |
| F3 | Pretraga brojeva (wildcard) |
| F4 | Rezervacija broja (5 min) |
| F5 | Dodjela kupcu + JMBG validacija |
| F6 | Kvaliteta broja (silver/gold/platinum/diamond) |
| F7 | Karantena oslobođenih brojeva |
| F8 | Županijski fallback |
| F9 | PDF ugovor i račun |
| F10 | Portal kupca (JMBG, pregled, PDF) |

### 3.3. Nefunkcionalni zahtjevi

- REST API, JSON, JWT  
- Responzivno sučelje, dark mode  
- Performanse pretrage na velikom inventaru (~600k redova)  
- Demo podaci — nije produkcijski SLA  

---

## 4. KORIŠTENE TEHNOLOGIJE I ALATI

| Sloj | Tehnologija |
|------|-------------|
| Backend | Python 3, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Baza | PostgreSQL |
| Auth | JWT (python-jose), bcrypt |
| PDF | ReportLab, DejaVu fontovi |
| Scheduler | APScheduler (rezervacije, karantena) |
| Frontend | React 19, TypeScript, Vite, Tailwind, Radix UI |
| Vizualizacija | Leaflet (mapa), Recharts (grafikoni) |
| Testiranje | pytest, httpx |
| Dev | Vite proxy `/api` → port 8004 |

*(Detaljno proširiti u v2 — usporedbe s Kapec/Marković)*

---

## 5. PROJEKTIRANJE SUSTAVA

### 5.1. Arhitektura

Tro-slojni model: SPA (React) ↔ REST API (FastAPI) ↔ PostgreSQL.

### 5.2. Hijerarhija podataka

Entitet → Županija → Općina → Lokacija → Uređaj (MSAN/OLT) → Raspon → MSISDN.

Statusi MSISDN: `slobodan`, `zauzet`, `karantena`.

### 5.3. Tok dodjele

1. Odabir općine i kvalitete  
2. `POST /rezerviraj-sljedeci`  
3. Unos kupca, `GET /msisdn/provjeri-jmbg`  
4. `POST /dodijeli-broj`  
5. Status zauzet, PDF ugovor  

*(U v2: ER dijagram, Mermaid u prilogu)*

---

## 6. IMPLEMENTACIJA

### 6.1. Backend (`msisdn_service.py`)

- `_find_slobodan_ids` — općina, zatim županijski pool  
- `rezerviraj_broj` / `rezerviraj_sljedeci_opcina`  
- `dodijeli_broj` — transakcija, PDF, email  

### 6.2. Frontend

- `/dodjela` — `DodjelaForma` i `DodjelaWizard` (isti API)  
- `/brojevi` — wildcard, URL sync filtera  
- `/portal` — odvojena prijava kupca  

### 6.3. Ograničenja demo sustava

- Mapa općina: bbox aproksimacija  
- Inventar: seed, ne produkcijski RAK snapshot  
- Email: Mailtrap u dev-u  

---

## 7. TESTIRANJE I REZULTATI

- **pytest:** 202 passed, 1 skipped  
- **Ručno:** prijava admin, wildcard `*1234`, dashboard, dodjela, portal (vidi `EVALUACIJA_KS.md`)  
- **Završno izvješće projekta:** ciljevi ostvareni bez odstupanja  

---

## 8. ZAKLJUČAK

Razvijen je funkcionalni prototip web sustava za inventar i dodjelu fiksnih brojeva koji ispunjava projektni zadatak prakse. Stečeno je iskustvo u full-stack razvoju, modeliranju telekom inventara i izradi korisničkog sučelja za operativne korisnike.

Budući rad: integracija s produkcijskim BSS, točne granice općina, proširenje sigurnosne revizije.

---

## 9. LITERATURA (radni popis)

1. Kapec, P. (2025). *Web-aplikacija za organizaciju događaja i rezervaciju termina*. FER, Zagreb.  
2. Maršić, B. (2023). *Sustav za upravljanje narudžbama korisnika telekom operatera*. FER, Zagreb.  
3. Čičić, M. (2020). *Analiza kvalitete usluge u UMTS mreži*. FPZ, Zagreb.  
4. FastAPI Documentation. https://fastapi.tiangolo.com/  
5. React Documentation. https://react.dev/  
6. PostgreSQL Documentation. https://www.postgresql.org/docs/  
7. HT d.d. Mostar (2026). *Projektni zadatak H104515959* (interni dokument).  
8. Baranašić, M. (2024). *Sigurnost i protokoli u razvoju web aplikacija*. FOI, Zagreb.  

---

## PRILOG A — API endpointi (dodjela)

| Metoda | Ruta | Opis |
|--------|------|------|
| POST | `/prijava` | JWT prijava |
| POST | `/rezerviraj-sljedeci` | Rezervacija |
| GET | `/msisdn/provjeri-jmbg` | JMBG |
| POST | `/dodijeli-broj` | Dodjela |
| GET | `/statistike` | Dashboard |
| GET | `/kupac/moji-brojevi` | Portal |

---

*Verzija 1.0 — 5. 8. 2026. — za FSRE / Boško Raguž*
