# UI stil — HT Eronet

## Paleta

| Token | Svijetli | Tamni |
|-------|----------|-------|
| Primary | `#0054A6` | `#0066cc` |
| Accent | `#00A3E0` | `#00A3E0` |
| Pozadina | gradient `#f8fafc` → `#eef4fb` | `#0f172a` → `#1e293b` |
| Tekst | `#0f172a` | `#f1f5f9` |
| Kartica | `bg-white` | `bg-slate-900` |

## Dark mode

- Klasa `dark` na `<html>` (hook `useDarkMode`, localStorage `eronet-dark-mode`).
- Tailwind: `@custom-variant dark (&:where(.dark, .dark *));`
- Toggle u headeru (Sun/Moon ikone).

## Animacije

- `AnimatedNumber` — brojači na dashboardu (800 ms, ease-out cubic).
- `fade-in` / `card-hover` — postojeći utility u `index.css`.

## Skeleton

- `Skeleton` — `animate-pulse`, `bg-slate-200` / `dark:bg-slate-700`.
- Zamjena za tekstualne "Učitavanje…" poruke.

## Print

- `@media print` u `index.css`: sakriva sidebar, header, gumbe (`.no-print`).
- Gumb **Ispiši** na Dashboardu i u detalju MSISDN-a.
