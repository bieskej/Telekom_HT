import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Layers, Search, ShieldAlert } from 'lucide-react'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'
import { api, mapApiError } from '@/lib/api'
import { FILTER_ALL, filterValueToApi } from '@/lib/constants'
import {
  parseBrojeviPageFromUrl,
  parseBrojeviStatusFromUrl,
  patchBrojeviSearchParams,
} from '@/lib/brojeviUrl'
import {
  pronadjiJedinstvenogKorisnika,
  pronadjiKorisnikaPoJmbg,
} from '@/lib/korisnikMatch'
import type { KorisnikItem, MsisdnItem, Opcina } from '@/types/api'
import { KorisnikDetaljiPanel } from '@/components/korisnici/KorisnikDetaljiPanel'
import { BrojeviTable } from '@/components/brojevi/BrojeviTable'
import { MsisdnDetaljModal } from '@/components/brojevi/MsisdnDetaljModal'
import { MagicBrojPretraga } from '@/components/brojevi/MagicBrojPretraga'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { OslobodiModal } from '@/components/oslobadanje/OslobodiModal'
import { Button, buttonVariants } from '@/components/ui/Button'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { EmptyState } from '@/components/ui/EmptyState'
import { StatusFilterChip } from '@/components/brojevi/StatusFilterChip'
import { MSISDN_STATUS_FILTER_OPTIONS } from '@/lib/statusUi'

const PER_PAGE = 20

export function BrojeviPage() {
  return (
    <ErrorBoundary title="Brojevi">
      <BrojeviPageInner />
    </ErrorBoundary>
  )
}

function BrojeviPageInner() {
  const { hasUloga } = useAuth()
  const mozeDodjela = hasUloga('admin', 'prodaja')
  const isAdmin = hasUloga('admin')
  const [detaljId, setDetaljId] = useState<number | null>(null)
  const [detaljOpen, setDetaljOpen] = useState(false)

  const [items, setItems] = useState<MsisdnItem[]>([])
  const [ukupno, setUkupno] = useState(0)
  const [loading, setLoading] = useState(true)
  const [broj, setBroj] = useState('')
  const [imePrezime, setImePrezime] = useState('')
  const [searchParams, setSearchParams] = useSearchParams()
  const [status, setStatus] = useState(() => parseBrojeviStatusFromUrl(searchParams))
  const [opcinaId, setOpcinaId] = useState(FILTER_ALL)
  const [opcinaPretraga, setOpcinaPretraga] = useState('')
  /** Točan naziv općine s karte (URL) dok nije mapiran na opcina_id. */
  const [opcinaIzUrlTocno, setOpcinaIzUrlTocno] = useState<string | null>(null)
  const [kvaliteta, setKvaliteta] = useState(FILTER_ALL)
  const [page, setPage] = useState(() => parseBrojeviPageFromUrl(searchParams))
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [karantenaOpen, setKarantenaOpen] = useState(false)
  const [karantenaIds, setKarantenaIds] = useState<number[]>([])
  const [opcine, setOpcine] = useState<Opcina[]>([])
  const [korisnici, setKorisnici] = useState<KorisnikItem[]>([])
  const [previewBrojevi, setPreviewBrojevi] = useState<MsisdnItem[]>([])
  const [loadingKorisnikBrojevi, setLoadingKorisnikBrojevi] = useState(false)

  const urlKorisnikJmbg = searchParams.get('korisnik_jmbg') ?? undefined
  const urlLokacijaId = searchParams.get('lokacija_id')
  const urlUredjajId = searchParams.get('uredjaj_id')
  const urlOpcinaNaziv = searchParams.get('opcina_naziv')?.trim() || null
  const urlOpcinaId = searchParams.get('opcina_id')?.trim() || null

  const urlFilterAktivan = Boolean(
    urlOpcinaNaziv || urlOpcinaId || urlLokacijaId || urlUredjajId,
  )

  useEffect(() => {
    api.korisnici().then(setKorisnici).catch(() => {})
  }, [])

  useEffect(() => {
    api
      .opcine()
      .then(setOpcine)
      .catch(() => setOpcine([]))
  }, [])

  const applyUrlPatch = useCallback(
    (patch: Parameters<typeof patchBrojeviSearchParams>[1]) => {
      setSearchParams(patchBrojeviSearchParams(searchParams, patch), { replace: true })
    },
    [searchParams, setSearchParams],
  )

  const ukloniUrlFilterOpcine = useCallback(() => {
    if (!searchParams.get('opcina_naziv') && !searchParams.get('opcina_id')) return
    applyUrlPatch({ clearOpcina: true })
  }, [searchParams, applyUrlPatch])

  /** Sync status i page iz URL-a (back/forward, dijeljeni link). */
  useEffect(() => {
    setStatus(parseBrojeviStatusFromUrl(searchParams))
    setPage(parseBrojeviPageFromUrl(searchParams))
  }, [searchParams])

  useEffect(() => {
    if (!urlOpcinaId && !urlOpcinaNaziv) {
      return
    }

    if (urlOpcinaId) {
      setOpcinaId(urlOpcinaId)
      setOpcinaPretraga('')
      setOpcinaIzUrlTocno(null)
      setPage(parseBrojeviPageFromUrl(searchParams))
      return
    }

    if (!urlOpcinaNaziv) return

    const match = opcine.find((o) => o.naziv.toLowerCase() === urlOpcinaNaziv.toLowerCase())
    if (match) {
      setOpcinaId(String(match.id))
      setOpcinaPretraga('')
      setOpcinaIzUrlTocno(null)
    } else {
      setOpcinaId(FILTER_ALL)
      setOpcinaPretraga('')
      setOpcinaIzUrlTocno(urlOpcinaNaziv)
    }
    const urlPage = parseBrojeviPageFromUrl(searchParams)
    setPage(urlPage)
  }, [urlOpcinaId, urlOpcinaNaziv, opcine, searchParams])

  const odabraniKorisnik = useMemo(() => {
    if (urlKorisnikJmbg) {
      return pronadjiKorisnikaPoJmbg(korisnici, urlKorisnikJmbg)
    }
    return pronadjiJedinstvenogKorisnika(korisnici, imePrezime)
  }, [korisnici, urlKorisnikJmbg, imePrezime])

  useEffect(() => {
    if (!odabraniKorisnik) {
      setPreviewBrojevi([])
      return
    }
    setLoadingKorisnikBrojevi(true)
    api
      .pretraga({ korisnik_jmbg: odabraniKorisnik.jmbg, per_page: 5, page: 1 })
      .then((res) => setPreviewBrojevi(res.rezultati ?? []))
      .catch(() => setPreviewBrojevi([]))
      .finally(() => setLoadingKorisnikBrojevi(false))
  }, [odabraniKorisnik?.jmbg])

  const ukloniFilterKorisnika = () => {
    const next = new URLSearchParams(searchParams)
    next.delete('korisnik_jmbg')
    setSearchParams(next)
    setImePrezime('')
    setPage(1)
  }

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const opcinaParam = filterValueToApi(opcinaId)
      const nazivFilter = opcinaPretraga.trim()
      const tocnoNaziv = opcinaIzUrlTocno?.trim()
      const opcinaFilterAktivan = Boolean(nazivFilter || opcinaParam || tocnoNaziv)
      const res = await api.pretraga({
        broj: broj || undefined,
        korisnik_ime_prezime: imePrezime.trim() || undefined,
        status: filterValueToApi(status),
        opcina_id: !nazivFilter && !tocnoNaziv && opcinaParam ? Number(opcinaParam) : undefined,
        opcina_naziv: tocnoNaziv || nazivFilter || undefined,
        opcina_naziv_tocno: tocnoNaziv ? 1 : undefined,
        kvaliteta: filterValueToApi(kvaliteta),
        korisnik_jmbg: urlKorisnikJmbg,
        lokacija_id:
          !opcinaFilterAktivan && urlLokacijaId ? Number(urlLokacijaId) : undefined,
        uredjaj_id:
          !opcinaFilterAktivan && urlUredjajId ? Number(urlUredjajId) : undefined,
        page,
        per_page: PER_PAGE,
      })
      setItems(res.rezultati ?? [])
      setUkupno(res.ukupno ?? 0)
    } catch (e) {
      setItems([])
      setUkupno(0)
      toast.error(mapApiError(e, 'Pretraga brojeva nije uspjela.'))
    } finally {
      setLoading(false)
    }
  }, [
    broj,
    imePrezime,
    status,
    opcinaId,
    opcinaPretraga,
    opcinaIzUrlTocno,
    kvaliteta,
    page,
    urlKorisnikJmbg,
    urlLokacijaId,
    urlUredjajId,
  ])

  useEffect(() => {
    void load()
  }, [load])

  const zauzetiOnly = useMemo(() => items.filter((i) => i.status === 'zauzet'), [items])
  const totalPages = Math.max(1, Math.ceil(ukupno / PER_PAGE))

  const opcineZaDropdown = useMemo(() => {
    const q = opcinaPretraga.trim().toLowerCase()
    if (!q) return opcine
    return opcine.filter((o) => o.naziv.toLowerCase().includes(q))
  }, [opcine, opcinaPretraga])

  const opcineOptions = useMemo(
    () => [
      { value: FILTER_ALL, label: 'Sve općine' },
      ...opcineZaDropdown.map((o) => ({
        value: String(o.id),
        label: `${o.naziv} (${(o.broj_msisdn ?? 0).toLocaleString('hr-HR')})`,
      })),
    ],
    [opcineZaDropdown],
  )

  useEffect(() => {
    if (!opcineOptions.some((o) => o.value === opcinaId)) {
      setOpcinaId(FILTER_ALL)
    }
  }, [opcineOptions, opcinaId])

  const openKarantena = (ids: number[]) => {
    setKarantenaIds(ids)
    setKarantenaOpen(true)
  }

  const openDetalj = (id: number) => {
    setDetaljId(id)
    setDetaljOpen(true)
  }

  const oslobodiKarantenaAdmin = async (id: number) => {
    if (!window.confirm('Osloboditi broj iz karantene? Broj postaje slobodan.')) return
    try {
      await api.oslobodiIzKarantene(id)
      toast.success('Broj je oslobođen iz karantene.')
      void load()
    } catch (e) {
      toast.error(mapApiError(e, 'Oslobađanje iz karantene nije uspjelo.'))
    }
  }

  const activeFilterHint = useMemo(() => {
    const nazivFilter = opcinaPretraga.trim()
    const opcinaParam = filterValueToApi(opcinaId)
    const tocnoNaziv = opcinaIzUrlTocno?.trim()
    const opcinaFilterAktivan = Boolean(nazivFilter || opcinaParam || tocnoNaziv)
    const parts: string[] = []
    if (tocnoNaziv) {
      parts.push(`Općina: ${tocnoNaziv}`)
    } else if (opcinaParam) {
      const o = opcine.find((x) => String(x.id) === opcinaParam)
      parts.push(`Općina: ${o?.naziv ?? urlOpcinaNaziv ?? `#${opcinaParam}`}`)
    } else if (urlOpcinaNaziv) {
      parts.push(`Općina: ${urlOpcinaNaziv}`)
    } else if (nazivFilter) {
      parts.push(`Općina (pretraga): ${nazivFilter}`)
    }
    if (urlLokacijaId && !opcinaFilterAktivan) parts.push(`Lokacija #${urlLokacijaId}`)
    if (urlUredjajId && !opcinaFilterAktivan) parts.push(`Uređaj #${urlUredjajId}`)
    return parts.length ? parts.join(' · ') : null
  }, [
    urlLokacijaId,
    urlUredjajId,
    urlOpcinaNaziv,
    opcinaPretraga,
    opcinaId,
    opcinaIzUrlTocno,
    opcine,
  ])

  return (
    <span className="block space-y-6">
      {mozeDodjela && !urlFilterAktivan && <MagicBrojPretraga />}

      {odabraniKorisnik && (
        <KorisnikDetaljiPanel
          korisnik={odabraniKorisnik}
          brojevi={previewBrojevi}
          loadingBrojevi={loadingKorisnikBrojevi}
          onZatvori={ukloniFilterKorisnika}
          sakrijLinkBrojeva={!!urlKorisnikJmbg}
        />
      )}

      {activeFilterHint && (
        <Card className="border-[#0054A6]/20 bg-[#0054A6]/5 p-4 text-sm text-[#0054A6]">
          Aktivni filter iz izbornika: {activeFilterHint}
        </Card>
      )}

      <Card className="p-4 lg:p-6">
        <span className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Input
            label="Broj (djelomično)"
            value={broj}
            onChange={(e) => {
              setBroj(e.target.value.replace(/\D/g, ''))
              setPage(1)
              applyUrlPatch({ page: 1 })
            }}
            placeholder="npr. 30304"
          />
          <Input
            label="Ime/Prezime"
            value={imePrezime}
            onChange={(e) => {
              setImePrezime(e.target.value)
              setPage(1)
              applyUrlPatch({ page: 1 })
            }}
            placeholder="Pretraga po korisniku"
          />
          <Select
            label="Status"
            value={status}
            onValueChange={(v) => {
              setStatus(v)
              setPage(1)
              applyUrlPatch({ status: v, page: 1 })
            }}
            options={[
              { value: FILTER_ALL, label: 'Svi statusi' },
              ...MSISDN_STATUS_FILTER_OPTIONS.map((o) => ({
                value: o.value,
                label: o.label,
              })),
            ]}
          />
          <Input
            label="Općina (pretraga)"
            value={opcinaPretraga}
            onChange={(e) => {
              ukloniUrlFilterOpcine()
              setOpcinaPretraga(e.target.value)
              setOpcinaId(FILTER_ALL)
              setOpcinaIzUrlTocno(null)
              setPage(1)
              applyUrlPatch({ page: 1, clearOpcina: true })
            }}
            placeholder="npr. Mostar — filtrira tablicu"
          />
          <Select
            label="Općina"
            value={opcinaId}
            onValueChange={(v) => {
              setOpcinaPretraga('')
              setOpcinaIzUrlTocno(null)
              setOpcinaId(v)
              setPage(1)
              if (v === FILTER_ALL) {
                applyUrlPatch({ clearOpcina: true, page: 1 })
              } else {
                const o = opcine.find((x) => String(x.id) === v)
                applyUrlPatch(
                  o
                    ? { opcinaNaziv: o.naziv, page: 1 }
                    : { opcinaId: v, page: 1 },
                )
              }
            }}
            options={opcineOptions}
          />
          <Select
            label="Kvaliteta"
            value={kvaliteta}
            onValueChange={(v) => {
              setKvaliteta(v)
              setPage(1)
              applyUrlPatch({ page: 1 })
            }}
            options={[
              { value: FILTER_ALL, label: 'Sve' },
              { value: 'silver', label: 'Silver' },
              { value: 'gold', label: 'Gold' },
              { value: 'platinum', label: 'Platinum' },
              { value: 'diamond', label: 'Diamond' },
            ]}
          />
        </span>
        <StatusFilterChip
          status={status}
          onClear={() => {
            setStatus(FILTER_ALL)
            setPage(1)
            applyUrlPatch({ status: FILTER_ALL, page: 1 })
          }}
        />
        <span className="mt-4 flex flex-wrap gap-3">
          <Button onClick={() => void load()}>
            <Search className="h-4 w-4" />
            Traži
          </Button>
          {mozeDodjela && (
            <>
              <Button
                variant="outline"
                onClick={() => openKarantena(Array.from(selected))}
                disabled={!selected.size}
              >
                <ShieldAlert className="h-4 w-4" />
                Stavi u karantenu odabrane ({selected.size})
              </Button>
              <Link
                to="/dodjela?bulk=1"
                className={cn(buttonVariants({ variant: 'accent', size: 'md' }))}
              >
                <Layers className="h-4 w-4" />
                Bulk dodjela
              </Link>
            </>
          )}
        </span>
      </Card>

      {loading ? (
        <TableSkeleton rows={8} />
      ) : items.length === 0 ? (
        <EmptyState
          title="Nema rezultata pretrage"
          description="Promijenite filtere (broj, status, općina, kvaliteta) ili uklonite filter s karte."
          action={mozeDodjela ? { label: 'Idi na dodjelu', to: '/dodjela' } : undefined}
        />
      ) : (
        <BrojeviTable
          items={items}
          selected={selected}
          onDetalj={openDetalj}
          isAdmin={isAdmin}
          prikaziOslobodiKarantena={status === 'karantena'}
          onOslobodiKarantena={(id) => void oslobodiKarantenaAdmin(id)}
          onSelect={(id, checked) => {
            setSelected((prev) => {
              const next = new Set(prev)
              if (checked) next.add(id)
              else next.delete(id)
              return next
            })
          }}
          onSelectAll={(checked) => {
            if (checked) setSelected(new Set(zauzetiOnly.map((r) => r.id)))
            else setSelected(new Set())
          }}
          zauzetiOnly={zauzetiOnly}
          mozeKarantena={mozeDodjela}
          onKarantena={(id) => openKarantena([id])}
        />
      )}

      <span className="flex flex-wrap items-center justify-center gap-4">
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => {
            const next = page - 1
            setPage(next)
            applyUrlPatch({ page: next })
          }}
        >
          Prethodna
        </Button>
        <span className="text-sm text-slate-600">
          Stranica {page} / {totalPages} ({ukupno.toLocaleString('hr-HR')} rezultata)
        </span>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => {
            const next = page + 1
            setPage(next)
            applyUrlPatch({ page: next })
          }}
        >
          Sljedeća
        </Button>
      </span>

      <OslobodiModal
        open={karantenaOpen}
        onOpenChange={setKarantenaOpen}
        msisdnIds={karantenaIds}
        onSuccess={() => {
          setSelected(new Set())
          void load()
        }}
      />
      <MsisdnDetaljModal
        msisdnId={detaljId}
        open={detaljOpen}
        onOpenChange={setDetaljOpen}
        onUpdated={() => void load()}
      />
    </span>
  )
}
