# UI stil — HT Eronet

Design system za staff aplikaciju i portal kupca. Prošireno za magistarski rad (KS). Status boje i zauzetost: `frontend/src/lib/statusUi.ts`.

---

## Paleta

| Token | Svijetli | Tamni |
|-------|----------|-------|
| Primary | `#0054A6` | `#0066cc` |
| Accent | `#00A3E0` | `#00A3E0` |
| Pozadina | gradient `#f8fafc` → `#eef4fb` | `#0f172a` → `#1e293b` |
| Tekst primarni | `#0f172a` / `slate-900` | `#f1f5f9` / `slate-100` |
| Tekst sekundarni | `slate-600` | `slate-400` |
| Kartica | `bg-white` | `bg-slate-900` |
| Obrub | `slate-200` | `slate-800` |

**Gradient primarni (gumbi, logo):** `from-[#0054A6] to-[#00A3E0]`.

---

## Tipografija

| Uloga | Klasa / veličina | Primjena |
|-------|------------------|----------|
| Naslov stranice | `text-lg`–`text-xl` `font-semibold` | Header `h1` |
| Naslov kartice | `CardTitle` — `font-semibold` | Sekcije |
| Tijelo | `text-sm` (14px) | Tablice, forme |
| Pomoćni tekst | `text-xs` `text-slate-500` | Hintovi, legenda |
| Brojevi / KPI | `text-3xl` `font-bold` | StatCards, AnimatedNumber |

**Font:** sistemski sans-serif (Tailwind default). Za rad: konzistentno `text-sm` u operativnim ekranima.

---

## Spacing (4/8 px)

| Token | Tailwind | Upotreba |
|-------|----------|----------|
| xs | `p-1`, `gap-1` (4px) | Ikone u gumbu |
| sm | `p-2`, `gap-2` (8px) | Kompaktni redovi |
| md | `p-4`, `gap-4` (16px) | Kartica unutra, form grid |
| lg | `p-6`–`p-8`, `lg:p-8` | Main layout padding |
| xl | `space-y-6`–`space-y-8` | Razmak između sekcija stranice |

**Zaobljenja:** gumbi/kartice `rounded-xl` (12px), inputi `rounded-[10px]`, badge `rounded-md`.

---

## Komponente — stanja

### Button (`components/ui/Button.tsx`)

| Stanje | Izgled |
|--------|--------|
| default | Primary gradient / plava pozadina |
| outline | Obrub, transparentna pozadina |
| ghost | Bez obruba, hover `slate` |
| disabled | `opacity-50`, `pointer-events-none` |
| focus | `focus-visible:ring-2 ring-[#00A3E0] ring-offset-2` |
| loading | Spinner, disabled |

### Input / Select (`Input.tsx`, `Select.tsx`)

| Stanje | Izgled / ponašanje |
|--------|---------------------|
| default | `border-slate-200`, visina `h-11`, dark varijante |
| label | `htmlFor` ↔ stabilni `id` (`useId`) |
| focus | `border-[#00A3E0]`, `ring-2 ring-[#00A3E0]/25` |
| error | prop `error?: string` → `border-red-500`, `aria-invalid`, `aria-describedby` na poruku (`role="alert"`) |
| disabled | Sivi obrub, reduced opacity |

### Dialog (`Dialog.tsx`, Radix)

| Značajka | Ponašanje |
|----------|-----------|
| Focus trap | Ugrađeno u `@radix-ui/react-dialog` — fokus ostaje u modalu |
| Escape | Zatvara dijalog (default Radix) |
| Overlay klik | Zatvara (`onOpenChange`) |
| Gumb X | `DialogPrimitive.Close`, `aria-label="Zatvori dijalog"` |

### API greške (`lib/apiErrors.ts`)

- `formatApiDetail(detail)` — FastAPI `detail` string ili validation array `{ loc, msg }`
- `mapApiError(e, fallback)` — za `toast.error` na Dashboard, Korisnici, Brojevi, Dodjela
- `api.request` baca `Error` s već formatiranom porukom

### Skeleton učitavanje

- `TableSkeleton` — Brojevi, Portabilnost
- `CardGridSkeleton` — Korisnici
- `Skeleton` — atom (`animate-pulse`)

### Card

- `shadow-[var(--shadow-card)]`, hover `card-hover` na dashboardu.
- Dark: `dark:bg-slate-900`, `dark:border-slate-800`.

---

## Status MSISDN (`lib/statusUi.ts`)

Korištenje: `MsisdnStatusBadge`, `Badge` variant, `msisdnStatusLabel()`, `StatusFilterChip` na /brojevi.

| Status | Label HR | Badge (Tailwind) | Hex |
|--------|----------|------------------|-----|
| `slobodan` | Slobodan | `bg-emerald-100 text-emerald-800` (+ dark varijante) | `#10b981` |
| `zauzet` | Zauzet | `bg-blue-100 text-[#0054A6]` | `#0054A6` |
| `karantena` | Karantena | `bg-amber-100 text-amber-800` | `#f59e0b` |
| `portano` | Portano | `bg-violet-100 text-violet-800` | `#7c3aed` |

API: `MSISDN_STATUS`, `msisdnBadgeClass()`, `MSISDN_STATUS_FILTER_OPTIONS`.

---

## Zauzetost općine (`bojaZaZauzetost`)

Mapa (`OpcinaMap`), grafikon (`OpcinaChart`), tablica ispod mape — ista legenda.

| Raspon | Opis | Hex |
|--------|------|-----|
| &lt; 50 % | Niska zauzetost | `#10b981` |
| 50 % – 90 % | Srednja | `#f59e0b` |
| ≥ 90 % | Visoka | `#dc2626` |

API: `ZAUZETOST_BOJE`, `ZAUZETOST_LEGENDA`, `bojaZaZauzetost(postotak)`.

---

## Prazna stanja (`components/ui/EmptyState.tsx`)

| Stranica | Naslov (primjer) | CTA |
|----------|------------------|-----|
| Korisnici | Nema korisnika / Nema za filter | Idi na dodjelu (ako nema nikoga) |
| Brojevi | Nema rezultata pretrage | Idi na dodjelu (prodaja/admin) |
| Portabilnost | Nema zahtjeva | — |
| Servisni nalozi | Nema naloga | — |
| Magični broj | Nema slobodnih brojeva | — |

---

## Dark mode

- Klasa `dark` na `<html>` (hook `useDarkMode`, localStorage `eronet-dark-mode`).
- Tailwind: `@custom-variant dark (&:where(.dark, .dark *));`
- Toggle u headeru (Sun/Moon ikone), `aria-label="Tamni način"`.

### WCAG napomene (dark mode)

| Element | Status (Faza 5) |
|---------|------------------|
| `text-slate-500` na tamnoj pozadini | Zamijenjeno s `text-slate-400` / `text-slate-600` gdje treba |
| Select dropdown | `dark:bg-slate-900`, tamni item tekst |
| Tablice | `thead` `dark:bg-slate-800`, `dark:text-slate-300/400` |
| OpcinaMap legenda | `dark:bg-slate-900/95`, `dark:text-slate-400` |
| Toast (sonner) | `dark:` klase u `App.tsx` + `[data-sonner-toast]` u `index.css` |
| Portal | `PortalLayout`, `PortalAuthShell` — dark varijante |
| Chart / mapa | Tekstualna legenda + tablica ispod mape |

**Cilj:** WCAG 2.1 **AA** za normalan tekst (4.5:1), veliki tekst (3:1). Alat: axe DevTools, Lighthouse.

---

## Animacije

- `AnimatedNumber` — brojači na dashboardu (800 ms, ease-out cubic).
- `fade-in` / `card-hover` — utility u `index.css`.
- `stagger-1`…`stagger-4` — sekvencijalni ulazak kartica.

**KS smjernica:** animacije kratke (&lt; 300 ms) za feedback; izbjegavati blokiranje interakcije.

---

## Skeleton

- `Skeleton` — `animate-pulse`, `bg-slate-200` / `dark:bg-slate-700`.
- `TableSkeleton`, `CardGridSkeleton` — liste (Faza 3).

---

## Print

- `@media print` u `index.css`: sakriva sidebar, header, navigaciju, gumbe (`.no-print`, `.print-hide`).
- **Dashboard:** gumb **Ispiši** — ispisuje KPI, heatmap i grafikon; **mapa se ne ispisuje** (`.print-hide-map` / `.leaflet-container`).
- Pozadina ispisa: bijela, tamni način se ne prenosi na papir.
- Napomena za korisnike: sekcija Dashboard na `/pomoc`.

---

## Ikone

- **Lucide React** — konzistentan stroke, `h-4 w-4` (gumbi), `h-5 w-5` (nav).

---

## Toast (sonner)

- Pozicija: `top-right`.
- Greške: koristiti poruku iz API `detail` (Faza 3), ne generički "Greška".

---

## Informacijska arhitektura (Faza 4)

| Element | Lokacija |
|---------|----------|
| Pomoć | `/pomoc` — `HelpPage.tsx`, sidebar + header `?` |
| Demo banner | `DemoBanner.tsx` u `Layout` — `DEV` ili `VITE_DEMO_BANNER=true` |
| Breadcrumbs | `Breadcrumbs.tsx` + `lib/breadcrumbRoutes.ts` |
| URL filteri /brojevi | `lib/brojeviUrl.ts` — `status`, `page`, `opcina_naziv` |

---

## Povezano

- [EVALUACIJA_KS.md](../../docs/EVALUACIJA_KS.md) — evaluacija KS
- [USER_FLOWS.md](../../docs/USER_FLOWS.md) — tokovi korisnika
