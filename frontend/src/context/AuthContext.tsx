import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { authStorage, type StoredRadnik, type Uloga } from '@/lib/authStorage'

interface AuthContextValue {
  radnik: StoredRadnik | null
  isAuthenticated: boolean
  prijava: (email: string, lozinka: string) => Promise<void>
  odjava: () => void
  hasUloga: (...uloge: Uloga[]) => boolean
  osvjeziToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

const REFRESH_BEFORE_MS = 7 * 60 * 60 * 1000 // 7 sati

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const [radnik, setRadnik] = useState<StoredRadnik | null>(() => authStorage.getRadnik())

  const prijava = useCallback(
    async (email: string, lozinka: string) => {
      const res = await api.prijava(email, lozinka)
      authStorage.setToken(res.access_token, res.expires_in)
      authStorage.setRadnik(res.radnik as StoredRadnik)
      authStorage.setCredentials({ email, lozinka })
      setRadnik(res.radnik as StoredRadnik)
      navigate('/', { replace: true })
    },
    [navigate],
  )

  const odjava = useCallback(() => {
    authStorage.clear()
    setRadnik(null)
    navigate('/prijava', { replace: true })
  }, [navigate])

  const osvjeziToken = useCallback(async () => {
    const creds = authStorage.getCredentials()
    if (!creds) return
    const res = await api.prijava(creds.email, creds.lozinka)
    authStorage.setToken(res.access_token, res.expires_in)
    authStorage.setRadnik(res.radnik as StoredRadnik)
    setRadnik(res.radnik as StoredRadnik)
  }, [])

  const hasUloga = useCallback(
    (...uloge: Uloga[]) => {
      if (!radnik) return false
      return uloge.includes(radnik.uloga)
    },
    [radnik],
  )

  useEffect(() => {
    const interval = setInterval(() => {
      const expiresAt = authStorage.getExpiresAt()
      if (!expiresAt || !authStorage.isAuthenticated()) return
      const remaining = expiresAt - Date.now()
      if (remaining > 0 && remaining < REFRESH_BEFORE_MS) {
        osvjeziToken().catch(() => odjava())
      }
    }, 60_000)
    return () => clearInterval(interval)
  }, [osvjeziToken, odjava])

  const value = useMemo(
    () => ({
      radnik,
      isAuthenticated: !!radnik && authStorage.isAuthenticated(),
      prijava,
      odjava,
      hasUloga,
      osvjeziToken,
    }),
    [radnik, prijava, odjava, hasUloga, osvjeziToken],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth mora biti unutar AuthProvider')
  return ctx
}
