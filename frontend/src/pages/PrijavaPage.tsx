import { useState } from 'react'

import { Navigate } from 'react-router-dom'

import { toast } from 'sonner'

import { useAuth } from '@/context/AuthContext'

import { mapApiError } from '@/lib/api'

import { Button } from '@/components/ui/Button'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'

import { Input } from '@/components/ui/Input'



export function PrijavaPage() {

  const { prijava, isAuthenticated } = useAuth()

  const [email, setEmail] = useState('admin@eronet.ba')

  const [lozinka, setLozinka] = useState('')

  const [loading, setLoading] = useState(false)

  const [emailError, setEmailError] = useState<string | undefined>()

  const [lozinkaError, setLozinkaError] = useState<string | undefined>()



  if (isAuthenticated) {

    return <Navigate to="/" replace />

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

      toast.error(mapApiError(err, 'Prijava nije uspjela. Provjerite email i lozinku.'))

    } finally {

      setLoading(false)

    }

  }



  return (

    <div className="flex min-h-screen items-center justify-center p-4">

      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-[#0054A6]/10 via-white to-[#00A3E0]/10" />

      <Card className="w-full max-w-md animate-fade-in shadow-[var(--shadow-modal)]">

        <CardHeader className="text-center">

          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl gradient-primary text-xl font-bold text-white shadow-lg">

            HT

          </div>

          <CardTitle className="text-2xl text-[#0054A6]">HT Eronet</CardTitle>

          <p className="text-sm text-slate-500">Prijava u sustav dodjele brojeva</p>

        </CardHeader>

        <CardContent>

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

          <p className="mt-4 text-center text-xs text-slate-400">Demo: admin@eronet.ba / admin</p>

        </CardContent>

      </Card>

    </div>

  )

}


