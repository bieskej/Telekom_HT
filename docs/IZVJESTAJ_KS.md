# Izvještaj — dorade korisničkog sučelja (KS, faze 1–7)

Kratak pregled rada na HT Eronet frontendu i pratećoj dokumentaciji za magistarski rad (kolegij *Korisnička sučelja*). **Nije** zamjena za poglavlje evaluacije sa sudionicima — vidi [EVALUACIJA_KS.md](EVALUACIJA_KS.md).

---

## Faza 1 — Pristupačnost i vizualna jasnoća

- Servisni nalozi: HTML5 drag-and-drop, „Premjesti u”, `aria-live` na Kanbanu  
- Mapa/dashboard: legenda zauzetosti (`lib/zauzetostUi.ts`), boje usklađene s grafikonima  
- Mapa: tablica top 15 općina uz choropleth (bbox aproksimacija)

## Faza 2 — Konzistentni statusi i prazna stanja

- `lib/statusUi.ts`, `MsisdnStatusBadge`, `EmptyState`  
- Primjena na Brojevi, Korisnici, Portabilnost, Servisni, Magični broj

## Faza 3 — Forme, greške, učitavanje

- `Input`/`Select`: `htmlFor`, poruke grešaka, ARIA  
- `lib/apiErrors.ts` + `mapApiError` u toastima  
- Skeleton tablice, dokumentacija `Dialog`, dark toast

## Faza 4 — Navigacija i pomoć

- `/pomoc` (`HelpPage`), `DemoBanner`, `Breadcrumbs`  
- URL sync na `BrojeviPage` (`lib/brojeviUrl.ts`)  
- Prošireni [USER_FLOWS.md](USER_FLOWS.md)

## Faza 5 — Portal kupca

- `PortalAuthShell`, dark `PortalLayout`  
- Inline validacija registracije (`portalValidation.ts`)  
- `PortalMojiBrojeviPage` + EmptyState, dark audit komponenti

## Faza 6 — Priprema evaluacije (dev)

- `/admin/eval-priprema` (admin + `import.meta.env.DEV`)  
- `data/evalPriprema.ts`, checklist export u MD  
- Protokol u [EVALUACIJA_KS.md](EVALUACIJA_KS.md)

## Faza 7 — Dva pristupa dodjeli

- `DodjelaWizard.tsx` (3 koraka), toggle na `DodjelaPage`  
- Isti API i success modal kao `DodjelaForma`  
- Scenarij **T4w** u evaluacijskom protokolu

## Faza 8 — QA i paket (ovo poglavlje)

- Smoke: backend + frontend, proxy `/api`, pytest **202 passed**  
- Ručni prolaz T1–T8 označen u [EVALUACIJA_KS.md](EVALUACIJA_KS.md) (QA 2026-06-02)  
- README sekcija „Magistarski rad (KS)”, ovaj izvještaj

---

## Preporuka za evaluaciju u radu

1. **Think-aloud + SUS** na 5–8 sudionika prema protokolu u EVALUACIJA_KS.md; usporedi **T4** (brza forma) i **T4w** (čarobnjak) za istu personu P1.  
2. **Heuristička evaluacija** (Nielsen + D1–D3) — 3 neovisna evaluatora; konsolidiraj probleme prije/poslije faza 1–2.  
3. **Ne tvrdi** da je mapa administrativno točna — istakni bbox demo i Crnići kao primjer visoke zauzetosti (T2).  
4. **Portal (T8):** prije sesije pokreni `python -m scripts.demo_seed_faza5` ili dodijeli broj s JMBG-om koji kupac registrira.  
5. **Artefakti:** screenshoti iz README liste + tablica vremena/grešaka + 3–5 citata + SUS bar chart (staff vs portal).

---

## Povezano

- [EVALUACIJA_KS.md](EVALUACIJA_KS.md)  
- [USER_FLOWS.md](USER_FLOWS.md)  
- [frontend/docs/UI_STIL.md](../frontend/docs/UI_STIL.md)  
- [README.md](../README.md) — Magistarski rad (KS)
