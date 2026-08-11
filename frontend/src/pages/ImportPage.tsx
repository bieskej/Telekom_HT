import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { ImportPostanskiForm } from '@/components/admin/ImportPostanskiForm'
import { ImportRakForm } from '@/components/admin/ImportRakForm'

export function ImportPage() {
  const { hasUloga } = useAuth()

  if (!hasUloga('admin')) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <p className="text-slate-600">Uvoz podataka u sustav. Dostupno samo administratorima.</p>
      <ImportPostanskiForm />
      <ImportRakForm />
    </div>
  )
}
