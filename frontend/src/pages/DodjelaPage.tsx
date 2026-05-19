import { Navigate, useSearchParams } from 'react-router-dom'
import { DodjelaForma } from '@/components/dodjela/DodjelaForma'
import { useAuth } from '@/context/AuthContext'

export function DodjelaPage() {
  const { hasUloga } = useAuth()
  const [searchParams] = useSearchParams()
  const rawId = searchParams.get('msisdn_id')
  const parsed = rawId ? Number(rawId) : NaN
  const initialMsisdnId = Number.isFinite(parsed) ? parsed : undefined

  if (!hasUloga('admin', 'prodaja')) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="mx-auto max-w-4xl">
      <p className="mb-6 text-slate-600">
        Unesite podatke korisnika. Broj se automatski rezervira na 5 minuta dok popunjavate formu.
      </p>
      <DodjelaForma initialMsisdnId={initialMsisdnId} />
    </div>
  )
}
