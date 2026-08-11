import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { toast } from 'sonner'
import { usePortalAuth } from '@/context/PortalAuthContext'
import { mapApiError } from '@/lib/api'
import { PortalAuthShell } from '@/components/portal/PortalAuthShell'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export function PortalPrijavaPage() {
  const { prijava, isAuthenticated } = usePortalAuth()
  const [email, setEmail] = useState('')
  const [lozinka, setLozinka] = useState('')
  const [loading, setLoading] = useState(false)
  const [emailError, setEmailError] = useState<string | undefined>()
  const [lozinkaError, setLozinkaError] = useState<string | undefined>()

  if (isAuthenticated) {
    return <Navigate to="/portal/moji-brojevi" replace />
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const eErr = !email.trim() ? 'Email je obavezan.' : undefined
    const lErr = !lozinka ? 'Lozinka je obavezna.' : undefined
    setEmailError(eErr)
    setLozinkaError(lErr)
    if (eErr || lErr) return

    setLoading(true)
    try {
      await prijava(email, lozinka)
      toast.success('Uspješna prijava')
    } catch (err) {
      toast.error(mapApiError(err, 'Prijava nije uspjela.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <PortalAuthShell
      title="Portal za kupce"
      subtitle="Pregled vaših telefonskih brojeva"
      footer={
        <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-400">
          Nemate račun?{' '}
          <Link
            to="/portal/registracija"
            className="font-medium text-[#0054A6] hover:underline dark:text-[#00A3E0]"
          >
            Registrirajte se
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            setEmailError(undefined)
          }}
          error={emailError}
          required
        />
        <Input
          label="Lozinka"
          type="password"
          autoComplete="current-password"
          value={lozinka}
          onChange={(e) => {
            setLozinka(e.target.value)
            setLozinkaError(undefined)
          }}
          error={lozinkaError}
          required
        />
        <Button type="submit" loading={loading} className="w-full" size="lg">
          Prijavi se
        </Button>
      </form>
    </PortalAuthShell>
  )
}
