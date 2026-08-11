const TOKEN_KEY = 'eronet_token'
const EXPIRES_KEY = 'eronet_token_expires'
const RADNIK_KEY = 'eronet_radnik'
const CREDS_KEY = 'eronet_credentials'

export type Uloga = 'admin' | 'prodaja' | 'promet' | 'kupac'

export interface StoredRadnik {
  id: number
  email: string
  ime: string
  prezime: string
  uloga: Uloga
  aktivan: boolean
}

export interface StoredCredentials {
  email: string
  lozinka: string
}

export const authStorage = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token: string, expiresInSeconds: number) => {
    localStorage.setItem(TOKEN_KEY, token)
    const expiresAt = Date.now() + expiresInSeconds * 1000
    localStorage.setItem(EXPIRES_KEY, String(expiresAt))
  },
  getExpiresAt: () => {
    const v = localStorage.getItem(EXPIRES_KEY)
    return v ? Number(v) : 0
  },
  getRadnik: (): StoredRadnik | null => {
    const raw = localStorage.getItem(RADNIK_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as StoredRadnik
    } catch {
      return null
    }
  },
  setRadnik: (radnik: StoredRadnik) => localStorage.setItem(RADNIK_KEY, JSON.stringify(radnik)),
  setCredentials: (creds: StoredCredentials) =>
    localStorage.setItem(CREDS_KEY, JSON.stringify(creds)),
  getCredentials: (): StoredCredentials | null => {
    const raw = localStorage.getItem(CREDS_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as StoredCredentials
    } catch {
      return null
    }
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(EXPIRES_KEY)
    localStorage.removeItem(RADNIK_KEY)
    localStorage.removeItem(CREDS_KEY)
  },
  isAuthenticated: () => !!localStorage.getItem(TOKEN_KEY),
}
