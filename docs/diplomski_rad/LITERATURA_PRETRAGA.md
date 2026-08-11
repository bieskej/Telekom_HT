# Dubinska pretraga sličnih radova — HT Eronet dodjela brojeva

**Projekt:** web aplikacija za upravljanje inventarom i automatsku dodjelu fiksnih telefonskih brojeva (općina → lokacija → uređaj → raspon → MSISDN).  
**Datum pretrage:** 5. 8. 2026.  
**Izvori:** DABAR, ZIR, FER, FOI, ETFOS, PMFST, CROSBI (ograničeno), Google Scholar / Exa, Theseus (FI), GitHub (akademski projekti).

---

## Sažetak zaključka

| Pitanje | Odgovor |
|---------|---------|
| Postoji li rad **izravno** kao tvoj (fiksna numeracija + web + rezervacija + dodjela + hijerarhija MSAN)? | **Ne** u hrvatskim repozitorijima — nema identičnog diplomskog/završnog rada. |
| Najbliži domenski | Radovi o **rezervaciji resursa** (FER 2025), **telekom procesima/narudžbama** (FER 2023), **inventaru mobilne mreže** (VVG 2020), **fixed-line provisioning** (Theseus / Kina). |
| Najbliži tehnološki | **React + PostgreSQL + JWT** (FER Kapec 2025, FOI Novak 2023, UNIRI Marković 2025); **React + REST + Python backend** (FER Papeš SmartHome); **FastAPI + React + PostgreSQL** — uglavnom blogovi/GitHub predlošci, rijetko HR diplomski. |
| Preporuka za rad | Kombiniraj **domenske** reference (BSS/NMS, MSISDN, ENUM/E.164) iz literature + **metodološke** iz rezervacijskih web aplikacija + **implementacijske** iz React/PostgreSQL radova. |

---

## Tablica pronađenih radova

| # | Naslov | Autor | God. | Vrsta | Sveučilište / izvor | Sličnost (1–5) | URL |
|---|--------|-------|------|-------|---------------------|----------------|-----|
| 1 | Web-aplikacija za organizaciju događaja i rezervaciju termina | Petar Kapec | 2025 | Završni (preddiplomski) | FER Zagreb | **4** | https://repozitorij.fer.unizg.hr/islandora/object/fer:13640 |
| 2 | Sustav za upravljanje narudžbama korisnika telekom operatera | Bruno Maršić | 2023 | Završni (preddiplomski) | FER Zagreb | **3** | https://zir.nsk.hr/islandora/object/fer:11417 |
| 3 | UPRAVITELJ INVENTAROM MOBILNE MREŽE — mobilna aplikacija za Android | Irena Knežević | 2020 | Završni (stručni) | VVG Virovitica | **3** | https://zir.nsk.hr/islandora/object/vsmti:542 |
| 4 | Razvoj kognitivne usluge u prostoru Interneta stvari (SmartHome) | Dominik Papeš | — | Diplomski / završni | FER Zagreb (Zavod za telekomunikacije) | **3** | https://repozitorij.fer.unizg.hr/islandora/object/fer:12617 |
| 5 | Usporedba obrade prikaza… (React + Vite + ASP.NET + PostgreSQL) | — | 2023 | Diplomski | FOI Varaždin | **3** | https://repozitorij.foi.unizg.hr/object/foi:9044 |
| 6 | Development of a Reservation Management System | Goran Marković | 2025 | Završni | UNIRI (Repozitorij Rijeka) | **4** | https://repozitorij.uniri.hr/islandora/object/infri:1697 |
| 7 | Progresivna web-aplikacija za rezervaciju termina u zdravstvenim ustanovama | — | — | Diplomski | FER Zagreb | **3** | https://repozitorij.unizg.hr/object/fer:9264 |
| 8 | IZRADA WEB STRANICE ZA REZERVACIJU NOGOMETNIH TERMINA | — | — | Završni | Sveuč. Sj. Bosna i Hercegovina (OSSST) | **3** | https://zir.nsk.hr/object/ossst:3197 |
| 9 | Web aplikacija za rezervaciju dijeljenih radnih mjesta | — | 2021 | Diplomski | FERIT Osijek | **3** | https://repozitorij.etfos.hr/object/etfos:3230 |
| 10 | Analiza kvalitete usluge u UMTS mreži (MSISDN, FNR, HLR) | Mislav Čičić | 2020 | Završni | FPZ Zagreb | **2** | https://zir.nsk.hr/islandora/object/fpz:1921 |
| 11 | Mobile number portability based on direct routing | Slaven Brčić | 2007 | Diplomski | FER Zagreb | **2** | https://repozitorij.fer.unizg.hr/ (ZIR/exa) |
| 12 | Number portability | Andrijana Popić | 2020 | Diplomski | FERIT Osijek | **2** | https://exa.ai/library/publication/fmbntml4kvv |
| 13 | The Research And Implementation Of Number Identification System Based On Web Service | — | — | Diplomski (Kina) | Globethesis / Theseus | **3** | https://globethesis.com/?t=2178330335960204 |
| 14 | Design And Implementation Of Integrated Communications Services Building Information Management System | — | — | Diplomski (Kina) | Globethesis | **4** | https://globethesis.com/?t=2308330473952223 |
| 15 | Business Support System Integration (NMS modul) | — | — | Diplomski (FI) | Theseus | **4** | https://www.theseus.fi/bitstream/handle/10024/101579/BSS%20integration.pdf |
| 16 | Telephone number assignment system (Calitel) | Felipe V. | — | Projekt / GitHub | Univerzitet (Kolumbija) | **5*** | https://github.com/felipevcc/telephone-system |
| 17 | Razvoj web aplikacije za praćenje ISS-a (Flask + Leaflet) | — | — | Završni | PMF Split | **2** | https://repozitorij.pmfst.unist.hr/object/pmfst:2215 |
| 18 | Sigurnost i protokoli u razvoju web aplikacija | Mihael Baranašić | 2024 | Završni | FOI Varaždin | **2** | https://urn.nsk.hr/urn:nbn:hr:211:320167 |
| 19 | Model primjene potpomognute komunikacije… telekom korisnička služba | — | — | Diplomski | FER Zagreb | **2** | https://repozitorij.fer.unizg.hr/object/fer:13287 |
| 20 | Web aplikacija za produktivnost (Django REST + React + PostgreSQL + JWT) | — | 2026 | Završni | UNIRI FIT | **3** | https://repository.inf.uniri.hr/object/infri:1697 |

\* #16 nije formalni diplomski rad u HR repozitoriju, ali je **najbliži funkcionalno** (dodjela brojeva po geografskim područjima).

**Legenda sličnosti:** 5 = vrlo sličan (dodjela/upravljanje brojevima); 4 = blizak (rezervacija + web + sličan poslovni tok); 3 = djelomičan (telekom ILI rezervacija ILI isti stog); 2 = teorija telekoma / metodologija rada; 1 = nevezano.

---

## Detaljni opisi (po važnosti za tvoj rad)

### 1. Kapec — Web-aplikacija za organizaciju događaja i rezervaciju termina (FER, 2025) — sličnost **4**

**Sažetak:** Full-stack aplikacija s ulogama (organizator/kupac), rezervacijom termina, JWT autentifikacijom, React + Tailwind + Vite na frontendu, Spring Boot + PostgreSQL na backendu. ENUM tipovi u bazi za status rezervacije i uloge.

**Zašto je relevantan:** Ista logika **vremenski ograničene rezervacije** i **više uloga** kao kod tvoje 5-min rezervacije broja i admin/prodaja/kupac. Odličan uzorak za poglavlje o zahtjevima, ER modelu i sigurnosti.

**Reference za poglavlja:** arhitektura, JWT, PostgreSQL ENUM/statusi, struktura rada (zahtjevi → dizajn → implementacija → testiranje).

---

### 2. Globethesis — Integrated Communications / fixed-line newly installed business — sličnost **4**

**Sažetak:** Sustav za **novoinstalirane fiksne linije**: registracija korisnika, **odabir telefonskog broja**, promjena broja, upit povijesti usluga. B/S arhitektura.

**Zašto je relevantan:** Najbliži **poslovni opis dodjele fiksnog broja** u akademskoj literaturi (iako nije HR i vjerojatno stariji stack).

**Reference:** uvod (problem), funkcionalni zahtjevi, usporedba s tradicionalnim OSS/BSS.

---

### 3. Theseus — BSS Integration (Number Management System modul) — sličnost **4**

**Sažetak:** Integracija order management sustava s **Number Management System** — rezervacija i oslobađanje MSISDN brojeva, XML/JSON API, dio BSS lanca (CLM → NMS).

**Zašto je relevantan:** Terminologija i **životni ciklus broja** (reserve → assign → release) direktno mapira na tvoj `rezerviraj` / `dodijeli-broj` / karantena.

**Reference:** teorijski dio (BSS/OSS), dijagram toka dodjele, usporedba s industrijskim NIMS rješenjima (Netaxis, Cerillion — vidi web, nisu diplomski).

---

### 4. GitHub — felipevcc/telephone-system — sličnost **5** (projekt, ne diplomski)

**Sažetak:** Mikroservisni sustav za **dodjelu telefonskih brojeva** kupcima po **geografskim područjima** (četvrti), residential/commercial, availability po centrali.

**Zašto je relevantan:** Funkcionalno gotovo paralelan tvom projektu (inventar, područje, dodjela). Koristi se kao **inspiracija za use case**, ne kao citat „diplomski rad”.

---

### 5. Maršić — Sustav za upravljanje narudžbama telekom operatera (FER, 2023) — sličnost **3**

**Sažetak:** Procesno-orijentirana aplikacija za **aktivaciju telekom usluge**; Spring Boot, PostgreSQL, Flowable BPMN.

**Zašto je relevantan:** Isti **domen (telekom operator)**, druga faza lanca (narudžba/aktivacija umjesto numeracije). Dobar za uvod i kontekst HT Eronet.

---

### 6. Knežević — Upravitelj inventarom mobilne mreže (VVG, 2020) — sličnost **3**

**Sažetak:** Mobilna aplikacija za tehničare — pregled **site-ova**, inventar mreže, zadataka održavanja; MS SQL + PHP.

**Zažetak:** Inventar telekom **uređaja/lokacija**, ne numeracija — korisno za hijerarhiju općina/lokacija/MSAN u teoriji.

---

### 7. Marković / UNIRI — Reservation Management System (2025) — sličnost **4**

**Sažetak:** NestJS + PostgreSQL + React + JWT + bcrypt; višerazinska autorizacija, Docker.

**Zašto je relevantan:** Moderni **full-stack obrazac** blizak tvom (samo NestJS umjesto FastAPI).

---

### 8. Papeš — SmartHome (FER, Zavod za telekomunikacije) — sličnost **3**

**Sažetak:** React klijent, Python backend, REST API, MVC — zadatak s FER Zavoda za telekomunikacije.

**Zašto je relevantan:** **Mentorski/institucionalni kontekst** sličan telekom modulima; dobar uzorak strukture FER radova.

---

### 9. Čičić — Analiza kvalitete usluge UMTS (FPZ, 2020) — sličnost **2**

**Sažetak:** Objašnjava **MSISDN**, HLR, FNR (vez MSISDN–IMSI), kvaliteta usluge u 3G.

**Reference:** teorijsko poglavlje o **MSISDN** i registrima (ne web implementacija).

---

### 10. Brčić / Popić — Number portability — sličnost **2**

**Sažetak:** Tehnička i tržišna analiza **prenosivosti broja** (MNP).

**Napomena:** Tvoj projekt portabilnost ima, ali ne fokusiraj se na ove radove osim ako proširuješ literaturu.

---

### 11. Baranašić — Sigurnost i protokoli u web aplikacijama (FOI, 2024) — sličnost **2**

**Sažetak:** HTTPS, TLS, sigurnost web aplikacija — **uzorak formata rada** (naslovnica, izjava, sažetak, sadržaj, poglavlja).

**Zašto je relevantan:** Primjer koji si stavio u folder — koristi za **formalnu strukturu** diplomskog/završnog rada FOI/SUM stila.

---

## Preporuka po poglavljima tvog rada

| Poglavlje | Preporučene reference |
|-----------|----------------------|
| **Uvod / problem** | Maršić (2023), BSS Theseus, Netaxis NIMS (web dokumentacija) |
| **Teorija telekoma** | Čičić MSISDN/FNR; E.164/ENUM (ITU-T preporuke); RAK/regulatorni okvir BiH |
| **Zahtjevi** | Kapec (2025) — tablica funkcionalnih zahtjeva; Globethesis fixed-line |
| **Arhitektura** | Kapec, Marković, FOI SSR (9044); Three-tier + REST |
| **Baza / hijerarhija** | Knežević (inventar); Cerillion/Sunvizion (mrežni inventar — industrijski) |
| **Rezervacija i dodjela** | Kapec, Marković, BSS NMS modul; felipevcc (use case) |
| **Implementacija (FastAPI/React)** | Papeš (React+REST); UNIRI Django+React+PG; FastAPI docs |
| **Sigurnost (JWT, JMBG)** | Baranašić (2024); Kapec JWT |
| **Testiranje** | Kapec; vlastiti pytest (202 testa) |
| **Zaključak** | Usporedba s odsutnošću identičnog HR rada + doprinos demo BSS modula |

---

## Pretraga po repozitorijima — napomene

| Repozitorij | Rezultat |
|-------------|----------|
| **dabar.srce.hr** | Nema direktnog pogotka „telefonska numeracija web”; generalno React/PostgreSQL rezervacije |
| **zir.nsk.hr** | Telekom narudžbe, inventar mobilne mreže, MNP, MSISDN u teoriji |
| **repozitorij.fer.unizg.hr** | Najviše telekom + web (SmartHome, virtualni asistent, rezervacije 2025) |
| **repozitorij.foi.unizg.hr** | React/TypeScript/Next — metodologija, ne telekom numeracija |
| **repozitorij.etfos.hr** | Rezervacije resursa, uloge — analogija |
| **repozitorij.pmfst.unist.hr** | Flask/React/Leaflet — korisno za mapu zauzetosti |
| **crosbi.hr** | Ograničen indeks; preporuka ručnog upita „MSISDN” / „telekomunikacije web aplikacija” |
| **FSRE Mostar** | Nema javnog repozitorija radova kao FER; koristi **interni** primjer + ovaj projekt |

---

## Međunarodna proširenja (IEEE/ACM)

Pretraga „number inventory management thesis” vodi na **industrijske whitepaper-e** (Netaxis NIMS, SaskTel Optius, Cerillion) više nego na IEEE papers. Za akademski rad citiraj 1–2 industrijska izvora + 2–3 diplomska iz tablice.

---

## Sljedeći koraci

1. Preuzmi PDF-ove s otvorenim pristupom (#1 Kapec, #4 Papeš, #18 Baranašić kao format).  
2. U diplomskom radu u uvodu eksplicitno navedi: *„Pretraga repozitorija FER, ZIR, FOI i međunarodnih baza nije identificirala rad s identičnom temom; najbliži su radovi o rezervaciji resursa i BSS number management modulima.“*  
3. Koristi `DIPLOMSKI_RAD_v1.md` kao prvu verziju teksta.
