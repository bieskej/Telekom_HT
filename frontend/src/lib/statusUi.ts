/**
 * Centralizirane boje i labele statusa (MSISDN, zauzetost općina).
 * Vidi frontend/docs/UI_STIL.md
 */

export type MsisdnStatus = 'slobodan' | 'zauzet' | 'karantena' | 'portano'

export interface MsisdnStatusUi {
  label: string
  /** Tailwind klase za Badge */
  badge: string
  /** Hex za grafove / SVG */
  hex: string
}

export const MSISDN_STATUS: Record<MsisdnStatus, MsisdnStatusUi> = {
  slobodan: {
    label: 'Slobodan',
    badge: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300',
    hex: '#10b981',
  },
  zauzet: {
    label: 'Zauzet',
    badge: 'bg-blue-100 text-[#0054A6] dark:bg-blue-950/80 dark:text-blue-300',
    hex: '#0054A6',
  },
  karantena: {
    label: 'Karantena',
    badge: 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300',
    hex: '#f59e0b',
  },
  portano: {
    label: 'Portano',
    badge: 'bg-violet-100 text-violet-800 dark:bg-violet-950/80 dark:text-violet-300',
    hex: '#7c3aed',
  },
}

export const MSISDN_STATUS_FILTER_OPTIONS = [
  { value: 'slobodan', label: MSISDN_STATUS.slobodan.label },
  { value: 'zauzet', label: MSISDN_STATUS.zauzet.label },
  { value: 'karantena', label: MSISDN_STATUS.karantena.label },
  { value: 'portano', label: MSISDN_STATUS.portano.label },
] as const

export function isMsisdnStatus(status: string): status is MsisdnStatus {
  return status in MSISDN_STATUS
}

export function msisdnStatusLabel(status: string): string {
  if (isMsisdnStatus(status)) return MSISDN_STATUS[status].label
  return status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' ')
}

export function msisdnBadgeVariant(status: string): MsisdnStatus | 'default' {
  return isMsisdnStatus(status) ? status : 'default'
}

export function msisdnBadgeClass(status: string): string {
  const v = msisdnBadgeVariant(status)
  if (v === 'default') return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
  return MSISDN_STATUS[v].badge
}

export function msisdnStatusHex(status: string): string {
  if (isMsisdnStatus(status)) return MSISDN_STATUS[status].hex
  return '#64748b'
}

/** Zauzetost inventara po općini (mapa, grafikon, tablice). */
export const ZAUZETOST_BOJE = {
  niska: '#10b981',
  srednja: '#f59e0b',
  visoka: '#dc2626',
} as const

export function bojaZaZauzetost(postotak: number): string {
  if (postotak >= 90) return ZAUZETOST_BOJE.visoka
  if (postotak >= 50) return ZAUZETOST_BOJE.srednja
  return ZAUZETOST_BOJE.niska
}

/** @deprecated Koristi bojaZaZauzetost */
export const bojaZaPostotak = bojaZaZauzetost

export const ZAUZETOST_LEGENDA = [
  { label: 'manje od 50%', boja: ZAUZETOST_BOJE.niska },
  { label: '50% – 90%', boja: ZAUZETOST_BOJE.srednja },
  { label: '90% i više', boja: ZAUZETOST_BOJE.visoka },
] as const
