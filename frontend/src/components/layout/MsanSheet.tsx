import { Search, Server } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import { Sheet } from '@/components/ui/Sheet'
import type { MsanUredjajItem } from '@/types/api'

interface MsanSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Desni slide-over panel "MSAN uređaji". Pretraga + lista kartica.
 * Klik na karticu vodi na /brojevi?uredjaj_id=<id> i zatvara panel.
 */
export function MsanSheet({ open, onOpenChange }: MsanSheetProps) {
  const navigate = useNavigate()
  const [pretraga, setPretraga] = useState('')
  const [uredjaji, setUredjaji] = useState<MsanUredjajItem[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    api
      .msanUredjaji()
      .then(setUredjaji)
      .catch(() => setUredjaji([]))
      .finally(() => setLoading(false))
  }, [open])

  const filtrirano = useMemo(() => {
    const q = pretraga.trim().toLowerCase()
    if (!q) return uredjaji
    return uredjaji.filter(
      (u) =>
        u.naziv.toLowerCase().includes(q) ||
        u.opcina_naziv.toLowerCase().includes(q),
    )
  }, [uredjaji, pretraga])

  const otvoriUredjaj = (id: number) => {
    onOpenChange(false)
    navigate(`/brojevi?uredjaj_id=${id}`)
  }

  return (
    <Sheet
      open={open}
      onOpenChange={onOpenChange}
      title="MSAN uređaji"
      description="Pretraga po nazivu uređaja ili općini"
    >
      <div className="mb-3 flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
        <Search className="h-4 w-4 text-slate-400" />
        <input
          type="text"
          value={pretraga}
          onChange={(e) => setPretraga(e.target.value)}
          placeholder="Pretraži MSAN (naziv ili općina)…"
          className="flex-1 bg-transparent text-sm outline-none"
          autoFocus
        />
      </div>

      {loading && <p className="text-sm text-slate-400">Učitavanje uređaja…</p>}

      {!loading && filtrirano.length === 0 && (
        <p className="text-sm text-slate-400">Nema rezultata.</p>
      )}

      <div className="space-y-2">
        {filtrirano.map((u) => (
          <button
            key={u.id}
            type="button"
            onClick={() => otvoriUredjaj(u.id)}
            className="flex w-full items-start gap-3 rounded-lg border border-slate-200 px-3 py-2.5 text-left transition hover:border-[#0054A6] hover:bg-[#0054A6]/5"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#0054A6]/10 text-[#0054A6]">
              <Server className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-800">
                {u.naziv}
              </p>
              <p className="truncate text-xs text-slate-500">
                {u.opcina_naziv}
              </p>
            </div>
            <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
              {u.kapacitet}
            </span>
          </button>
        ))}
      </div>
    </Sheet>
  )
}
