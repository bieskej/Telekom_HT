import type { KupacMojiBrojeviResponse, PrijavaResponse } from '@/types/api'
import { portalAuthStorage } from '@/lib/portalAuthStorage'

const BASE = import.meta.env.VITE_API_URL ?? '/api'

async function portalRequest<T>(path: string, init?: RequestInit & { skipAuth?: boolean }): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string>),
  }
  if (!init?.skipAuth) {
    const token = portalAuthStorage.getToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }
  const res = await fetch(`${BASE}${path}`, { ...init, headers })
  if (res.status === 401 && !init?.skipAuth) {
    portalAuthStorage.clear()
    window.location.href = '/portal/prijava'
    throw new Error('Sesija je istekla.')
  }
  if (!res.ok) {
    let detail = 'Došlo je do greške.'
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      detail = res.statusText
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

async function portalDownloadPdf(path: string, filename: string): Promise<void> {
  const token = portalAuthStorage.getToken()
  const res = await fetch(`${BASE}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (res.status === 401) {
    portalAuthStorage.clear()
    window.location.href = '/portal/prijava'
    throw new Error('Sesija je istekla.')
  }
  if (!res.ok) {
    let detail = 'Preuzimanje nije uspjelo.'
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      detail = res.statusText
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export const portalApi = {
  registracija: (body: {
    ime: string
    prezime: string
    email: string
    jmbg: string
    lozinka: string
  }) =>
    portalRequest<PrijavaResponse['radnik']>('/kupac/registracija', {
      method: 'POST',
      body: JSON.stringify(body),
      skipAuth: true,
    }),

  prijava: (email: string, lozinka: string) =>
    portalRequest<PrijavaResponse>('/kupac/prijava', {
      method: 'POST',
      body: JSON.stringify({ email, lozinka }),
      skipAuth: true,
    }),

  mojiBrojevi: (stranica = 1) =>
    portalRequest<KupacMojiBrojeviResponse>(
      `/kupac/moji-brojevi?stranica=${stranica}&velicina=20`,
    ),

  preuzmiUgovor: (msisdnId: number) =>
    portalDownloadPdf(`/kupac/ugovor/${msisdnId}`, `ugovor_${msisdnId}.pdf`),

  kontakt: (predmet: string, poruka: string) =>
    portalRequest<{ id: number; poruka: string }>('/kupac/kontakt', {
      method: 'POST',
      body: JSON.stringify({ predmet, poruka }),
    }),
}
