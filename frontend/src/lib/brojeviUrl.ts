import { FILTER_ALL } from '@/lib/constants'

export interface BrojeviUrlPatch {
  status?: string
  page?: number
  opcinaNaziv?: string | null
  opcinaId?: string | null
  clearOpcina?: boolean
}

/** Primijeni filtere u query string; zadržava ostale parametre (korisnik_jmbg, lokacija_id, …). */
export function patchBrojeviSearchParams(
  current: URLSearchParams,
  patch: BrojeviUrlPatch,
): URLSearchParams {
  const next = new URLSearchParams(current)

  if (patch.clearOpcina) {
    next.delete('opcina_naziv')
    next.delete('opcina_id')
  }

  if (patch.opcinaNaziv !== undefined) {
    next.delete('opcina_id')
    if (patch.opcinaNaziv) next.set('opcina_naziv', patch.opcinaNaziv)
    else next.delete('opcina_naziv')
  }

  if (patch.opcinaId !== undefined) {
    next.delete('opcina_naziv')
    if (patch.opcinaId) next.set('opcina_id', patch.opcinaId)
    else next.delete('opcina_id')
  }

  if (patch.status !== undefined) {
    if (!patch.status || patch.status === FILTER_ALL) next.delete('status')
    else next.set('status', patch.status)
  }

  if (patch.page !== undefined) {
    if (patch.page <= 1) next.delete('page')
    else next.set('page', String(patch.page))
  }

  return next
}

export function parseBrojeviPageFromUrl(searchParams: URLSearchParams): number {
  const p = Number(searchParams.get('page'))
  return p > 0 ? Math.floor(p) : 1
}

export function parseBrojeviStatusFromUrl(searchParams: URLSearchParams): string {
  return searchParams.get('status')?.trim() || FILTER_ALL
}
