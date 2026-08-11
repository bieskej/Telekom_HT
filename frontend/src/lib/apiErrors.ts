/**
 * Čitljive HR poruke iz FastAPI odgovora (polje detail).
 */

type FastApiValidationItem = {
  msg?: string
  loc?: (string | number)[]
  type?: string
}

export function formatApiDetail(detail: unknown): string {
  if (detail == null || detail === '') {
    return 'Došlo je do greške.'
  }
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    const parts = detail.map((item) => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object') {
        const v = item as FastApiValidationItem
        if (v.msg) {
          const loc = v.loc?.filter((x) => x !== 'body').map(String).join(' → ')
          return loc ? `${loc}: ${v.msg}` : v.msg
        }
      }
      return String(item)
    })
    const joined = parts.filter(Boolean).join(' ')
    return joined || 'Došlo je do greške.'
  }
  if (typeof detail === 'object') {
    const o = detail as Record<string, unknown>
    if (typeof o.message === 'string') return o.message
    if (typeof o.msg === 'string') return o.msg
  }
  return 'Došlo je do greške.'
}

/**
 * Mapira caught error u poruku za toast (koristi Error.message iz api.request).
 */
export function mapApiError(e: unknown, fallback = 'Došlo je do greške. Pokušajte ponovo.'): string {
  if (e instanceof Error) {
    const msg = e.message.trim()
    if (!msg) return fallback
    if (msg.startsWith('[')) {
      try {
        return formatApiDetail(JSON.parse(msg) as unknown)
      } catch {
        return msg
      }
    }
    return msg
  }
  if (typeof e === 'string' && e.trim()) return e.trim()
  return fallback
}
