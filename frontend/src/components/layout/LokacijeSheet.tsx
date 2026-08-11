import { ChevronDown, ChevronRight, MapPin, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { Sheet } from '@/components/ui/Sheet'
import type {
  HijerarhijaStabloOpcina,
  HijerarhijaStabloZupanija,
} from '@/types/api'

interface LokacijeSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Desni slide-over panel "Lokacije". Stablo Županija → Općina → Lokacija
 * s pretragom po nazivu. Klik na lokaciju vodi na /brojevi?lokacija_id=<id>
 * i zatvara panel.
 */
export function LokacijeSheet({ open, onOpenChange }: LokacijeSheetProps) {
  const navigate = useNavigate()
  const [pretraga, setPretraga] = useState('')
  const [stablo, setStablo] = useState<HijerarhijaStabloZupanija[]>([])
  const [loading, setLoading] = useState(false)
  const [expandedZup, setExpandedZup] = useState<Set<number>>(new Set())
  const [expandedOpc, setExpandedOpc] = useState<Set<number>>(new Set())

  useEffect(() => {
    if (!open) return
    setLoading(true)
    api
      .hijerarhijaStablo()
      .then(setStablo)
      .catch(() => setStablo([]))
      .finally(() => setLoading(false))
  }, [open])

  const filtrirano = useMemo(() => {
    const q = pretraga.trim().toLowerCase()
    if (!q) return stablo
    return stablo
      .map((z) => {
        const opcine = z.opcine
          .map((o) => {
            const lokacije = o.lokacije.filter(
              (l) =>
                l.naziv.toLowerCase().includes(q) ||
                o.naziv.toLowerCase().includes(q) ||
                z.naziv.toLowerCase().includes(q),
            )
            if (
              lokacije.length === 0 &&
              !o.naziv.toLowerCase().includes(q) &&
              !z.naziv.toLowerCase().includes(q)
            )
              return null
            return { ...o, lokacije } as HijerarhijaStabloOpcina
          })
          .filter((o): o is HijerarhijaStabloOpcina => o !== null)
        if (
          opcine.length === 0 &&
          !z.naziv.toLowerCase().includes(q) &&
          !z.oznaka.toLowerCase().includes(q)
        )
          return null
        return { ...z, opcine }
      })
      .filter((z): z is HijerarhijaStabloZupanija => z !== null)
  }, [stablo, pretraga])

  useEffect(() => {
    if (!pretraga.trim()) return
    const z = new Set<number>()
    const o = new Set<number>()
    filtrirano.forEach((zup) => {
      z.add(zup.id)
      zup.opcine.forEach((op) => o.add(op.id))
    })
    setExpandedZup(z)
    setExpandedOpc(o)
  }, [pretraga, filtrirano])

  const togleZ = (id: number) =>
    setExpandedZup((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  const togleO = (id: number) =>
    setExpandedOpc((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })

  const otvoriLokaciju = (lokacijaId: number) => {
    onOpenChange(false)
    navigate(`/brojevi?lokacija_id=${lokacijaId}`)
  }

  return (
    <Sheet
      open={open}
      onOpenChange={onOpenChange}
      title="Lokacije"
      description="Pretraga po županiji, općini ili nazivu lokacije"
    >
      <div className="mb-3 flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
        <Search className="h-4 w-4 text-slate-400" />
        <input
          type="text"
          value={pretraga}
          onChange={(e) => setPretraga(e.target.value)}
          placeholder="Pretraži lokaciju, općinu ili županiju…"
          className="flex-1 bg-transparent text-sm outline-none"
          autoFocus
        />
      </div>

      {loading && <p className="text-sm text-slate-400">Učitavanje stabla…</p>}

      {!loading && filtrirano.length === 0 && (
        <p className="text-sm text-slate-400">Nema rezultata.</p>
      )}

      <div className="space-y-1">
        {filtrirano.map((z) => (
          <div key={z.id}>
            <button
              type="button"
              onClick={() => togleZ(z.id)}
              className="flex w-full items-center gap-1 rounded-lg px-2 py-1.5 text-left text-sm font-semibold text-[#0054A6] hover:bg-[#0054A6]/8"
            >
              {expandedZup.has(z.id) ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
              <span className="truncate">{z.naziv}</span>
              <span className="ml-1 text-[10px] text-slate-400">({z.oznaka})</span>
            </button>
            {expandedZup.has(z.id) &&
              z.opcine.map((o) => (
                <div key={o.id} className="ml-3 border-l border-slate-100 pl-2">
                  <button
                    type="button"
                    onClick={() => togleO(o.id)}
                    className="flex w-full items-center gap-1 rounded px-2 py-1 text-left text-xs font-medium text-slate-700 hover:bg-slate-50"
                  >
                    {expandedOpc.has(o.id) ? (
                      <ChevronDown className="h-3 w-3" />
                    ) : (
                      <ChevronRight className="h-3 w-3" />
                    )}
                    <span className="truncate">{o.naziv}</span>
                    <span className="ml-1 text-[10px] text-slate-400">
                      {o.ukupno}
                    </span>
                  </button>
                  {expandedOpc.has(o.id) &&
                    o.lokacije.map((l) => (
                      <button
                        key={l.id}
                        type="button"
                        onClick={() => otvoriLokaciju(l.id)}
                        className="ml-4 flex w-full items-center gap-1.5 truncate rounded px-2 py-1 text-left text-xs text-slate-600 hover:bg-[#0054A6]/8 hover:text-[#0054A6]"
                      >
                        <MapPin className="h-3 w-3 shrink-0" />
                        <span className="truncate">{l.naziv}</span>
                        <span className="ml-auto text-[10px] text-slate-400">
                          {l.ukupno}
                        </span>
                      </button>
                    ))}
                </div>
              ))}
          </div>
        ))}
      </div>
    </Sheet>
  )
}
