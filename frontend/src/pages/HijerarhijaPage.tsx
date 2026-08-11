import { Search } from 'lucide-react'
import { Component, type ErrorInfo, type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import {
  HijerarhijaStablo,
  type OdabraniCvor,
} from '@/components/hijerarhija/HijerarhijaStablo'
import { HijerarhijaDetalj } from '@/components/hijerarhija/HijerarhijaDetalj'
import { api } from '@/lib/api'
import type {
  HijerarhijaCvorDetalj,
  HijerarhijaCvorTip,
  HijerarhijaStabloZupanija,
} from '@/types/api'

class HijerarhijaErrorBoundary extends Component<
  { children: ReactNode },
  { error: string | null }
> {
  state = { error: null as string | null }

  static getDerivedStateFromError(err: Error) {
    return { error: err.message }
  }

  componentDidCatch(err: Error, info: ErrorInfo) {
    console.error('HijerarhijaPage:', err, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <Card>
          <CardContent className="p-8 text-sm text-red-600">
            Greška prikaza hijerarhije: {this.state.error}
          </CardContent>
        </Card>
      )
    }
    return this.props.children
  }
}

const VALJANI_TIPOVI: HijerarhijaCvorTip[] = [
  'zupanija',
  'opcina',
  'lokacija',
  'uredjaj',
]

/**
 * Master-detail prikaz administrativne hijerarhije.
 * - Lijevo (1/3): stablo Županija → Općina → Lokacija → MSAN
 * - Desno (2/3): metrike i uzorak MSISDN-a odabranog čvora
 * - Odabir je u URL query parametrima: `?tip=lokacija&id=5`
 */
export function HijerarhijaPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [stablo, setStablo] = useState<HijerarhijaStabloZupanija[]>([])
  const [loadingStablo, setLoadingStablo] = useState(true)
  const [detalj, setDetalj] = useState<HijerarhijaCvorDetalj | null>(null)
  const [loadingDetalj, setLoadingDetalj] = useState(false)
  const [pretraga, setPretraga] = useState('')

  const odabrani = useMemo<OdabraniCvor | null>(() => {
    const tip = searchParams.get('tip') as HijerarhijaCvorTip | null
    const idStr = searchParams.get('id')
    if (!tip || !idStr) return null
    if (!VALJANI_TIPOVI.includes(tip)) return null
    const id = Number(idStr)
    if (!Number.isFinite(id) || id <= 0) return null
    return { tip, id }
  }, [searchParams])

  const postaviOdabir = useCallback(
    (cvor: OdabraniCvor) => {
      setSearchParams({ tip: cvor.tip, id: String(cvor.id) })
    },
    [setSearchParams],
  )

  useEffect(() => {
    let cancelled = false
    setLoadingStablo(true)
    api
      .hijerarhijaStablo()
      .then((data) => {
        if (!cancelled) setStablo(Array.isArray(data) ? data : [])
      })
      .catch((e) => toast.error(e instanceof Error ? e.message : 'Greška'))
      .finally(() => {
        if (!cancelled) setLoadingStablo(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!odabrani) {
      setDetalj(null)
      setLoadingDetalj(false)
      return
    }
    let cancelled = false
    setLoadingDetalj(true)
    api
      .hijerarhijaCvor(odabrani.tip, odabrani.id)
      .then((data) => {
        if (!cancelled) setDetalj(data)
      })
      .catch((e) => {
        if (!cancelled) {
          toast.error(e instanceof Error ? e.message : 'Čvor nije pronađen')
          setDetalj(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingDetalj(false)
      })
    return () => {
      cancelled = true
    }
  }, [odabrani])

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-[#0054A6]">
          Administrativna hijerarhija
        </h1>
        <p className="text-sm text-slate-600">
          Stablo Županija → Općina → Lokacija → MSAN s uzorkom MSISDN-a po čvoru
        </p>
      </div>

      <HijerarhijaErrorBoundary>
      <div className="grid gap-4 lg:grid-cols-[minmax(320px,33%)_1fr]">
        <Card className="max-h-[calc(100vh-10rem)] overflow-hidden">
          <CardHeader className="space-y-2 py-3">
            <CardTitle className="text-base">Stablo</CardTitle>
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 px-2.5 py-1.5">
              <Search className="h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                value={pretraga}
                onChange={(e) => setPretraga(e.target.value)}
                placeholder="Pretraži stablo…"
                className="flex-1 bg-transparent text-sm outline-none"
              />
            </div>
          </CardHeader>
          <CardContent className="max-h-[calc(100vh-16rem)] overflow-y-auto p-2">
            {loadingStablo && (
              <p className="p-4 text-sm text-slate-400">Učitavanje…</p>
            )}
            {!loadingStablo && (
              <HijerarhijaStablo
                stablo={stablo}
                pretraga={pretraga}
                odabrani={odabrani}
                onOdabir={postaviOdabir}
              />
            )}
          </CardContent>
        </Card>

        <HijerarhijaDetalj detalj={detalj} loading={loadingDetalj} />
      </div>
      </HijerarhijaErrorBoundary>
    </div>
  )
}
