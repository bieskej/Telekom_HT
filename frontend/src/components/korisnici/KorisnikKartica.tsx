import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronDown, UserCircle } from 'lucide-react'
import { api } from '@/lib/api'
import { FILTER_ALL, filterValueToApi } from '@/lib/constants'
import type { KorisnikItem, MsisdnItem } from '@/types/api'
import { useAuth } from '@/context/AuthContext'
import { IzlazKaranteneModal } from '@/components/korisnici/IzlazKaranteneModal'
import { ProduziKarantenuModal } from '@/components/korisnici/ProduziKarantenuModal'
import { OslobodiModal } from '@/components/oslobadanje/OslobodiModal'
import { Badge, MsisdnStatusBadge } from '@/components/ui/Badge'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Select } from '@/components/ui/Select'
import { cn } from '@/lib/utils'

const PREVIEW_BROJEVA = 20

interface KorisnikKarticaProps {
  korisnik: KorisnikItem
  onRefresh?: () => void
}

export function KorisnikKartica({ korisnik, onRefresh }: KorisnikKarticaProps) {
  const { hasUloga } = useAuth()
  const mozeKarantena = hasUloga('admin', 'prodaja')
  const isAdmin = hasUloga('admin')

  const [otvoreno, setOtvoreno] = useState(false)
  const [statusFilter, setStatusFilter] = useState(FILTER_ALL)
  const [brojevi, setBrojevi] = useState<MsisdnItem[]>([])
  const [loadingBrojevi, setLoadingBrojevi] = useState(false)

  const [karantenaOpen, setKarantenaOpen] = useState(false)
  const [karantenaId, setKarantenaId] = useState<number | null>(null)
  const [produziOpen, setProduziOpen] = useState(false)
  const [produziId, setProduziId] = useState<number | null>(null)
  const [produziBroj, setProduziBroj] = useState<string>()
  const [izlazOpen, setIzlazOpen] = useState(false)
  const [izlazId, setIzlazId] = useState<number | null>(null)
  const [izlazBroj, setIzlazBroj] = useState<string>()

  const ucitajBrojeve = useCallback(() => {
    setLoadingBrojevi(true)
    const status = filterValueToApi(statusFilter)
    api
      .pretraga({
        korisnik_jmbg: korisnik.jmbg,
        ...(status ? { status } : {}),
        per_page: PREVIEW_BROJEVA,
        page: 1,
      })
      .then((res) => setBrojevi(res.rezultati ?? []))
      .catch(() => setBrojevi([]))
      .finally(() => setLoadingBrojevi(false))
  }, [korisnik.jmbg, statusFilter])

  useEffect(() => {
    if (!otvoreno) return
    ucitajBrojeve()
  }, [otvoreno, ucitajBrojeve])

  const nakonAkcije = () => {
    ucitajBrojeve()
    onRefresh?.()
  }

  const linkBrojevi = `/brojevi?korisnik_jmbg=${encodeURIComponent(korisnik.jmbg)}`

  return (
    <>
      <Card className={cn('overflow-hidden transition-shadow', otvoreno && 'ring-2 ring-[#00A3E0]/30')}>
        <div className="p-4">
          <div className="flex items-start gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#0054A6]/10 text-[#0054A6]">
              <UserCircle className="h-6 w-6" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-semibold text-slate-800">
                {korisnik.ime} {korisnik.prezime}
              </p>
              <p className="mt-1 font-mono text-xs text-slate-500">{korisnik.jmbg}</p>
              {korisnik.email && <p className="mt-1 truncate text-sm text-slate-500">{korisnik.email}</p>}
              <p className="mt-2 text-sm font-medium text-[#0054A6]">
                {korisnik.broj_brojeva}{' '}
                {korisnik.broj_brojeva === 1 ? 'dodijeljen broj' : 'dodijeljenih brojeva'}
                {korisnik.broj_zauzet > 0 && korisnik.broj_karantena > 0 && (
                  <span className="font-normal text-slate-500">
                    {' '}
                    ({korisnik.broj_zauzet} aktivno, {korisnik.broj_karantena} karantena)
                  </span>
                )}
              </p>
              {korisnik.broj_karantena > 0 && (
                <Badge variant="karantena" className="mt-2">
                  {korisnik.broj_karantena}{' '}
                  {korisnik.broj_karantena === 1 ? 'broj u karanteni' : 'broja u karanteni'}
                </Badge>
              )}
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setOtvoreno((v) => !v)}
            >
              <ChevronDown className={cn('h-4 w-4 transition-transform', otvoreno && 'rotate-180')} />
              {otvoreno ? 'Sakrij detalje' : 'Detalji'}
            </Button>
            <Link to={linkBrojevi}>
              <Button variant="ghost" size="sm" type="button">
                Svi brojevi
              </Button>
            </Link>
          </div>
        </div>
        {otvoreno && (
          <div className="border-t border-slate-100 bg-slate-50/50 px-4 pb-4 pt-3">
            <Select
              label="Filter brojeva"
              value={statusFilter}
              onValueChange={setStatusFilter}
              options={[
                { value: FILTER_ALL, label: 'Svi statusi' },
                { value: 'zauzet', label: 'Zauzet' },
                { value: 'karantena', label: 'Karantena' },
              ]}
              className="mb-3"
            />
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">Brojevi</p>
            {loadingBrojevi ? (
              <p className="text-sm text-slate-500">Učitavanje brojeva…</p>
            ) : brojevi.length === 0 ? (
              <EmptyState
                title="Nema brojeva za filter"
                description="Promijenite filter statusa ili pogledajte sve brojeve korisnika."
                className="border-0 bg-transparent p-4 shadow-none"
              />
            ) : (
              <ul className="space-y-2">
                {brojevi.map((b) => (
                  <li
                    key={b.id}
                    className="rounded-lg bg-white px-3 py-2 text-sm shadow-sm"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-medium text-slate-800">{b.broj_formatiran}</span>
                      <MsisdnStatusBadge status={b.status} />
                    </div>
                    {mozeKarantena && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {b.status === 'zauzet' && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setKarantenaId(b.id)
                              setKarantenaOpen(true)
                            }}
                          >
                            Stavi u karantenu
                          </Button>
                        )}
                        {b.status === 'karantena' && (
                          <>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setProduziId(b.id)
                                setProduziBroj(b.broj_formatiran)
                                setProduziOpen(true)
                              }}
                            >
                              Produži karantenu
                            </Button>
                            <Button
                              type="button"
                              variant="accent"
                              size="sm"
                              onClick={() => {
                                setIzlazId(b.id)
                                setIzlazBroj(b.broj_formatiran)
                                setIzlazOpen(true)
                              }}
                            >
                              Izlaz iz karantene
                            </Button>
                          </>
                        )}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </Card>

      <OslobodiModal
        open={karantenaOpen}
        onOpenChange={setKarantenaOpen}
        msisdnIds={karantenaId != null ? [karantenaId] : []}
        onSuccess={nakonAkcije}
      />
      <ProduziKarantenuModal
        open={produziOpen}
        onOpenChange={setProduziOpen}
        msisdnId={produziId}
        brojFormatiran={produziBroj}
        onSuccess={nakonAkcije}
      />
      <IzlazKaranteneModal
        open={izlazOpen}
        onOpenChange={setIzlazOpen}
        msisdnId={izlazId}
        brojFormatiran={izlazBroj}
        isAdmin={isAdmin}
        onSuccess={nakonAkcije}
      />
    </>
  )
}
