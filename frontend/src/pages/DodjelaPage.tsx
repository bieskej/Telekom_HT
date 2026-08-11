import { useState } from 'react'

import { Layers, Sparkles } from 'lucide-react'

import { Navigate, useSearchParams } from 'react-router-dom'

import { DodjelaForma } from '@/components/dodjela/DodjelaForma'

import { DodjelaWizard } from '@/components/dodjela/DodjelaWizard'

import { BulkDodjelaModal } from '@/components/dodjela/BulkDodjelaModal'

import { useAuth } from '@/context/AuthContext'

import { Button } from '@/components/ui/Button'

import { cn } from '@/lib/utils'



type DodjelaNacin = 'brza' | 'wizard'



export function DodjelaPage() {

  const { hasUloga } = useAuth()

  const [searchParams] = useSearchParams()

  const rawId = searchParams.get('msisdn_id')

  const parsed = rawId ? Number(rawId) : NaN

  const initialMsisdnId = Number.isFinite(parsed) ? parsed : undefined

  const [bulkOpen, setBulkOpen] = useState(searchParams.get('bulk') === '1')

  const [nacin, setNacin] = useState<DodjelaNacin>('brza')



  if (!hasUloga('admin', 'prodaja')) {

    return <Navigate to="/" replace />

  }



  return (

    <div className="mx-auto max-w-4xl space-y-6">

      <div className="flex flex-wrap items-start justify-between gap-4">

        <div className="space-y-3">

          <p className="max-w-2xl text-slate-600 dark:text-slate-400">

            {nacin === 'brza'

              ? 'Sva polja na jednom ekranu. Broj se rezervira na 5 minuta dok popunjavate formu.'

              : 'Korak po korak: broj → kupac → plaćanje i potvrda (isti API kao brza forma).'}

          </p>

          <span className="inline-flex rounded-lg border border-slate-200 p-1 dark:border-slate-700">

            <button

              type="button"

              onClick={() => setNacin('brza')}

              className={cn(

                'rounded-md px-3 py-1.5 text-sm font-medium transition',

                nacin === 'brza'

                  ? 'bg-[#0054A6] text-white'

                  : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800',

              )}

            >

              Brza forma

            </button>

            <button

              type="button"

              onClick={() => setNacin('wizard')}

              className={cn(

                'inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-sm font-medium transition',

                nacin === 'wizard'

                  ? 'bg-[#0054A6] text-white'

                  : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800',

              )}

            >

              <Sparkles className="h-3.5 w-3.5" />

              Čarobnjak

            </button>

          </span>

        </div>

        <Button variant="outline" onClick={() => setBulkOpen(true)}>

          <Layers className="h-4 w-4" />

          Bulk dodjela

        </Button>

      </div>

      {nacin === 'brza' ? (

        <DodjelaForma initialMsisdnId={initialMsisdnId} />

      ) : (

        <DodjelaWizard initialMsisdnId={initialMsisdnId} />

      )}

      <BulkDodjelaModal open={bulkOpen} onOpenChange={setBulkOpen} />

    </div>

  )

}


