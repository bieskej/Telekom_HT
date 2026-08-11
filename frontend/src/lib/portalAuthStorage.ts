/** Odvojeno spremište sesije za portal kupaca (ne miješa se s radničkom aplikacijom). */

const TOKEN_KEY = 'eronet_portal_token'
const EXPIRES_KEY = 'eronet_portal_token_expires'
const KUPAC_KEY = 'eronet_portal_kupac'
const CREDS_KEY = 'eronet_portal_credentials'

export type PortalUloga = 'kupac'

export interface StoredKupac {
  id: number
  email: string
  ime: string
  prezime: string
  uloga: PortalUloga
  aktivan: boolean
  jmbg?: string | null
}

export interface PortalCredentials {
  email: string
  lozinka: string
}

export const portalAuthStorage = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token: string, expiresInSeconds: number) => {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(EXPIRES_KEY, String(Date.now() + expiresInSeconds * 1000))
  },
  getExpiresAt: () => {
    const v = localStorage.getItem(EXPIRES_KEY)
    return v ? Number(v) : 0
  },
  getKupac: (): StoredKupac | null => {
    const raw = localStorage.getItem(KUPAC_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as StoredKupac
    } catch {
      return null
    }
  },
  setKupac: (kupac: StoredKupac) => localStorage.setItem(KUPAC_KEY, JSON.stringify(kupac)),
  setCredentials: (creds: PortalCredentials) =>
    localStorage.setItem(CREDS_KEY, JSON.stringify(creds)),
  getCredentials: (): PortalCredentials | null => {
    const raw = localStorage.getItem(CREDS_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as PortalCredentials
    } catch {
      return null
    }
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(EXPIRES_KEY)
    localStorage.removeItem(KUPAC_KEY)
    localStorage.removeItem(CREDS_KEY)
  },
  isAuthenticated: () => !!localStorage.getItem(TOKEN_KEY),
}
