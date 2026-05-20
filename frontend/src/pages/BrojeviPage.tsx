import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Layers, Search, ShieldAlert } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import { FILTER_ALL, filterValueToApi } from '@/lib/constants'
import {
  pronadjiJedinstvenogKorisnika,
  pronadjiKorisnikaPoJmbg,
} from '@/lib/korisnikMatch'
import type { KorisnikItem, MsisdnItem, Opcina } from '@/types/api'
import { KorisnikDetaljiPanel } from '@/components/korisnici/KorisnikDetaljiPanel'
import { BrojeviTable } from '@/components/brojevi/BrojeviTable'
import { MsisdnDetaljModal } from '@/components/brojevi/MsisdnDetaljModal'
import { MagicBrojPretraga } from '@/components/brojevi/MagicBrojPretraga'
import { Skeleton } from '@/components/ui/Skeleton'
import { BulkDodjelaModal } from '@/components/dodjela/BulkDodjelaModal'
import { OslobodiModal } from '@/components/oslobadanje/OslobodiModal'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'

const PER_PAGE = 20

export function BrojeviPage() {
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
  const [status, setStatus] = useState(FILTER_ALL)
  const [opcinaId, setOpcinaId] = useState(FILTER_ALL)
  const [opcinaPretraga, setOpcinaPretraga] = useState('')
  const [kvaliteta, setKvaliteta] = useState(FILTER_ALL)
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [karantenaOpen, setKarantenaOpen] = useState(false)
  const [karantenaIds, setKarantenaIds] = useState<number[]>([])
  const [bulkOpen, setBulkOpen] = useState(false)
  const [opcine, setOpcine] = useState<Opcina[]>([])
  const [korisnici, setKorisnici] = useState<KorisnikItem[]>([])
  const [previewBrojevi, setPreviewBrojevi] = useState<MsisdnItem[]>([])
  const [loadingKorisnikBrojevi, setLoadingKorisnikBrojevi] = useState(false)

  const [searchParams, setSearchParams] = useSearchParams()
  const urlKorisnikJmbg = searchParams.get('korisnik_jmbg') ?? undefined
  const urlLokacijaId = searchParams.get('lokacija_id')
  const urlUredjajId = searchParams.get('uredjaj_id')

  useEffect(() => {
    api.korisnici().then(setKorisnici).catch(() => {})
  }, [])

  useEffect(() => {
    api
      .opcine()
      .then(setOpcine)
      .catch(() => setOpcine([]))
  }, [])

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
      const opcinaFilterAktivan = Boolean(nazivFilter || opcinaParam)
      const res = await api.pretraga({
        broj: broj || undefined,
        korisnik_ime_prezime: imePrezime.trim() || undefined,
        status: filterValueToApi(status),
        opcina_id: !nazivFilter && opcinaParam ? Number(opcinaParam) : undefined,
        opcina_naziv: nazivFilter || undefined,
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
      toast.error(e instanceof Error ? e.message : 'Greška pri pretrazi')
    } finally {
      setLoading(false)
    }
  }, [broj, imePrezime, status, opcinaId, opcinaPretraga, kvaliteta, page, urlKorisnikJmbg, urlLokacijaId, urlUredjajId])

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
      toast.error(e instanceof Error ? e.message : 'Greška')
    }
  }

  const activeFilterHint = useMemo(() => {
    const nazivFilter = opcinaPretraga.trim()
    const opcinaParam = filterValueToApi(opcinaId)
    const opcinaFilterAktivan = Boolean(nazivFilter || opcinaParam)
    const parts: string[] = []
    if (urlLokacijaId && !opcinaFilterAktivan) parts.push(`Lokacija #${urlLokacijaId}`)
    if (urlUredjajId && !opcinaFilterAktivan) parts.push(`Uređaj #${urlUredjajId}`)
    return parts.length ? parts.join(' · ') : null
  }, [urlLokacijaId, urlUredjajId, opcinaPretraga, opcinaId])

  return (
    <span className="block space-y-6">
      {mozeDodjela && <MagicBrojPretraga />}

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
            }}
            placeholder="npr. 30304"
          />
          <Input
            label="Ime/Prezime"
            value={imePrezime}
            onChange={(e) => {
              setImePrezime(e.target.value)
              setPage(1)
            }}
            placeholder="Pretraga po korisniku"
          />
          <Select
            label="Status"
            value={status}
            onValueChange={(v) => {
              setStatus(v)
              setPage(1)
            }}
            options={[
              { value: FILTER_ALL, label: 'Svi statusi' },
              { value: 'slobodan', label: 'Slobodan' },
              { value: 'zauzet', label: 'Zauzet' },
              { value: 'karantena', label: 'Karantena' },
            ]}
          />
          <Input
            label="Općina (pretraga)"
            value={opcinaPretraga}
            onChange={(e) => {
              setOpcinaPretraga(e.target.value)
              setOpcinaId(FILTER_ALL)
              setPage(1)
            }}
            placeholder="npr. Mostar — filtrira tablicu"
          />
          <Select
            label="Općina"
            value={opcinaId}
            onValueChange={(v) => {
              setOpcinaId(v)
              setOpcinaPretraga('')
              setPage(1)
            }}
            options={opcineOptions}
          />
          <Select
            label="Kvaliteta"
            value={kvaliteta}
            onValueChange={(v) => {
              setKvaliteta(v)
              setPage(1)
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
              <Button variant="accent" onClick={() => setBulkOpen(true)}>
                <Layers className="h-4 w-4" />
                Bulk dodjela
              </Button>
            </>
          )}
        </span>
      </Card>

      {loading ? (
        <span className="block space-y-3 py-8">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </span>
      ) : items.length === 0 ? (
        <Card className="p-8 text-center text-slate-500">Nema rezultata za odabrane filtere.</Card>
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
        <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          Prethodna
        </Button>
        <span className="text-sm text-slate-600">
          Stranica {page} / {totalPages} ({ukupno.toLocaleString('hr-HR')} rezultata)
        </span>
        <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
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
      <BulkDodjelaModal open={bulkOpen} onOpenChange={setBulkOpen} onSuccess={() => void load()} />
      <MsisdnDetaljModal
        msisdnId={detaljId}
        open={detaljOpen}
        onOpenChange={setDetaljOpen}
        onUpdated={() => void load()}
      />
    </span>
  )
}
