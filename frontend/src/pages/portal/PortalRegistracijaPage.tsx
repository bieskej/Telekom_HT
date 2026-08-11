import { useMemo, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { toast } from 'sonner'
import { usePortalAuth } from '@/context/PortalAuthContext'
import { mapApiError } from '@/lib/api'
import {
  inlineEmailError,
  inlineJmbgError,
  inlineLozinkaError,
  validirajEmail,
  validirajJmbg,
} from '@/lib/portalValidation'
import { PortalAuthShell } from '@/components/portal/PortalAuthShell'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export function PortalRegistracijaPage() {
  const { registracija, isAuthenticated } = usePortalAuth()
  const [ime, setIme] = useState('')
  const [prezime, setPrezime] = useState('')
  const [email, setEmail] = useState('')
  const [jmbg, setJmbg] = useState('')
  const [lozinka, setLozinka] = useState('')
  const [loading, setLoading] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<string, string>>>({})

  const emailInline = useMemo(() => inlineEmailError(email), [email])
  const jmbgInline = useMemo(() => inlineJmbgError(jmbg), [jmbg])
  const lozinkaInline = useMemo(() => inlineLozinkaError(lozinka), [lozinka])

  const clearFieldError = (key: string) => {
    setFieldErrors((p) => {
      const next = { ...p }
      delete next[key]
      return next
    })
  }

  if (isAuthenticated) {
    return <Navigate to="/portal/moji-brojevi" replace />
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const errs: Record<string, string> = {}
    if (!ime.trim()) errs.ime = 'Ime je obavezno.'
    if (!prezime.trim()) errs.prezime = 'Prezime je obavezno.'
    if (!email.trim()) errs.email = 'Email je obavezan.'
    else if (!validirajEmail(email)) errs.email = 'Unesite ispravnu email adresu.'
    if (jmbg.length !== 13 || !validirajJmbg(jmbg)) errs.jmbg = 'Unesite ispravan JMBG (13 znamenki).'
    if (!lozinka || lozinka.length < 4) errs.lozinka = 'Lozinka mora imati najmanje 4 znaka.'
    setFieldErrors(errs)
    if (Object.keys(errs).length > 0) return

    setLoading(true)
    try {
      await registracija({ ime, prezime, email, jmbg, lozinka })
      toast.success('Registracija uspješna')
    } catch (err) {
      toast.error(mapApiError(err, 'Registracija nije uspjela.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <PortalAuthShell
      title="Registracija kupca"
      subtitle="JMBG mora odgovarati brojevima u ugovoru"
      showLogo={false}
      footer={
        <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-400">
          Već imate račun?{' '}
          <Link to="/portal/prijava" className="font-medium text-[#0054A6] hover:underline dark:text-[#00A3E0]">
            Prijavite se
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-3" noValidate>
        <Input
          label="Ime"
          value={ime}
          onChange={(e) => {
            setIme(e.target.value)
            clearFieldError('ime')
          }}
          error={fieldErrors.ime}
          required
        />
        <Input
          label="Prezime"
          value={prezime}
          onChange={(e) => {
            setPrezime(e.target.value)
            clearFieldError('prezime')
          }}
          error={fieldErrors.prezime}
          required
        />
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            clearFieldError('email')
          }}
          error={fieldErrors.email ?? emailInline}
          required
        />
        <Input
          label="JMBG (13 znamenki)"
          value={jmbg}
          onChange={(e) => {
            setJmbg(e.target.value.replace(/\D/g, '').slice(0, 13))
            clearFieldError('jmbg')
          }}
          maxLength={13}
          error={fieldErrors.jmbg ?? jmbgInline}
          required
        />
        <Input
          label="Lozinka"
          type="password"
          autoComplete="new-password"
          value={lozinka}
          onChange={(e) => {
            setLozinka(e.target.value)
            clearFieldError('lozinka')
          }}
          minLength={4}
          error={fieldErrors.lozinka ?? lozinkaInline}
          required
        />
        <Button type="submit" loading={loading} className="w-full" size="lg">
          Registriraj se
        </Button>
      </form>
    </PortalAuthShell>
  )
}
