/**
 * Auth za portal kupaca — ODVOJEN od AuthContext (radnici).
 *
 * Odluka: zasebni localStorage ključevi (portalAuthStorage) jer kupac i radnik
 * mogu koristiti isti preglednik; zajednički token bi uzrokovao konflikt uloga
 * i pogrešan pristup rutama (/ vs /portal).
 */
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useNavigate } from 'react-router-dom'
import { portalApi } from '@/lib/portalApi'
import {
  portalAuthStorage,
  type StoredKupac,
} from '@/lib/portalAuthStorage'

interface PortalAuthContextValue {
  kupac: StoredKupac | null
  isAuthenticated: boolean
  prijava: (email: string, lozinka: string) => Promise<void>
  registracija: (podaci: {
    ime: string
    prezime: string
    email: string
    jmbg: string
    lozinka: string
  }) => Promise<void>
  odjava: () => void
}

const PortalAuthContext = createContext<PortalAuthContextValue | null>(null)

export function PortalAuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const [kupac, setKupac] = useState<StoredKupac | null>(() => portalAuthStorage.getKupac())

  const prijava = useCallback(
    async (email: string, lozinka: string) => {
      const res = await portalApi.prijava(email, lozinka)
      portalAuthStorage.setToken(res.access_token, res.expires_in)
      portalAuthStorage.setKupac(res.radnik as StoredKupac)
      portalAuthStorage.setCredentials({ email, lozinka })
      setKupac(res.radnik as StoredKupac)
      navigate('/portal/moji-brojevi', { replace: true })
    },
    [navigate],
  )

  const registracija = useCallback(
    async (podaci: {
      ime: string
      prezime: string
      email: string
      jmbg: string
      lozinka: string
    }) => {
      await portalApi.registracija(podaci)
      await prijava(podaci.email, podaci.lozinka)
    },
    [prijava],
  )

  const odjava = useCallback(() => {
    portalAuthStorage.clear()
    setKupac(null)
    navigate('/portal/prijava', { replace: true })
  }, [navigate])

  const value = useMemo(
    () => ({
      kupac,
      isAuthenticated: !!kupac && portalAuthStorage.isAuthenticated(),
      prijava,
      registracija,
      odjava,
    }),
    [kupac, prijava, registracija, odjava],
  )

  return (
    <PortalAuthContext.Provider value={value}>{children}</PortalAuthContext.Provider>
  )
}

export function usePortalAuth() {
  const ctx = useContext(PortalAuthContext)
  if (!ctx) throw new Error('usePortalAuth mora biti unutar PortalAuthProvider')
  return ctx
}
