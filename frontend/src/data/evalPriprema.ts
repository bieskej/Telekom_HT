/** Sadržaj za /admin/eval-priprema — iz docs/EVALUACIJA_KS.md (bez backend API-ja). */

export interface EvalScenario {
  id: string
  task: string
  persona: string
  startUrl: string
  success: string
}

export const EVAL_SCENARIOS: EvalScenario[] = [
  {
    id: 'T1',
    task: 'Prijava u staff sustav',
    persona: 'P1/P2',
    startUrl: '/prijava',
    success: 'Korisnik na dashboardu, vidi ime u headeru',
  },
  {
    id: 'T2',
    task: 'Na dashboardu pronađi općinu s zauzetosti ≥ 90%',
    persona: 'P2/P3',
    startUrl: '/',
    success: 'Nazove općinu i postotak (±2%)',
  },
  {
    id: 'T3',
    task: 'Pretraga broja wildcard *1234',
    persona: 'P1',
    startUrl: '/brojevi',
    success: 'Pronađe ≥1 rezultat, otvori detalj',
  },
  {
    id: 'T4',
    task: 'Dodjela: Mostar, silver, ispravan JMBG',
    persona: 'P1',
    startUrl: '/dodjela',
    success: 'Success modal, broj zauzet',
  },
  {
    id: 'T4w',
    task: 'Dodjela čarobnjak (3 koraka) — usporedi s T4',
    persona: 'P1',
    startUrl: '/dodjela',
    success: 'Isti kriterij kao T4 (toggle Čarobnjak)',
  },
  {
    id: 'T5',
    task: 'Korisnik s karantenom — produži 30 dana',
    persona: 'P1/P2',
    startUrl: '/korisnici',
    success: 'Broj u karanteni s novim rokom',
  },
  {
    id: 'T6',
    task: 'Servisni nalog → stupac Riješen',
    persona: 'P2',
    startUrl: '/servisni-nalozi',
    success: 'Status = riješen',
  },
  {
    id: 'T7',
    task: 'Hijerarhija → općina → Brojevi',
    persona: 'P2',
    startUrl: '/hijerarhija',
    success: 'Link na /brojevi s filterom općine',
  },
  {
    id: 'T8',
    task: 'Portal: prijava, brojevi, PDF ugovor',
    persona: 'P4',
    startUrl: '/portal/prijava',
    success: 'PDF preuzet ili jasna poruka',
  },
]

export const EVAL_TEST_ACCOUNTS = `HT Eronet — testni računi (dev)

Staff prijava: http://localhost:5173/prijava
Backend: http://127.0.0.1:8004

Admin:  admin@eronet.ba  /  admin
Prodaja: prodaja@eronet.ba  /  prodaja
Promet: promet@test.ba (kreirati u /radnici ako ne postoji)

Portal: http://localhost:5173/portal/prijava
Portal registracija: http://localhost:5173/portal/registracija

Demo JMBG (validan): 0101000500012

Prije T8: dodjela s istim JMBG-om ili python -m scripts.demo_seed_faza5 (backend)
`

export const SUS_FORM_URL =
  import.meta.env.VITE_SUS_FORM_URL?.trim() || ''

export const EVAL_CHECKLIST_MARKDOWN = `# Checklist testera — HT Eronet KS evaluacija

Sudionik: _______________  Datum: _______________  Uloga: _______________

## Priprema
- [ ] Backend pokrenut (port 8004)
- [ ] Frontend pokrenut (localhost:5173)
- [ ] Hard refresh na /prijava (Ctrl+Shift+R)
- [ ] Informirani pristanak potpisan

## Zadaci (think-aloud)
| ID | ✓ | ✗ | djel. | Vrijeme (s) | Greške | Bilješka |
|----|---|---|-------|-------------|--------|----------|
| T1 | [ ] | [ ] | [ ] | | | |
| T2 | [ ] | [ ] | [ ] | | | |
| T3 | [ ] | [ ] | [ ] | | | |
| T4 | [ ] | [ ] | [ ] | | | |
| T5 | [ ] | [ ] | [ ] | | | |
| T6 | [ ] | [ ] | [ ] | | | |
| T7 | [ ] | [ ] | [ ] | | | |
| T8 | [ ] | [ ] | [ ] | | | |

## SUS (1–5 po stavci)
- [ ] Stavke 1–10 ispunjene
- [ ] SUS skor izračunat

## Heuristike (Nielsen) — brzi pregled
- [ ] H1 Vidljivost statusa
- [ ] H2 Stvarni svijet
- [ ] H5 Prevencija grešaka
- [ ] H9 Oporavak od grešaka
- [ ] H10 Pomoć (/pomoc)

## Završni intervju
- [ ] Snimljeno 3–5 citata
- [ ] Najteži zadatak zabilježen
`
