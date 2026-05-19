import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import type { WildcardMsisdnItem } from '@/types/api'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'

const PRESETI = ['*7777', '*1234', '*0000', '*X0X0', '*XX'] as const

export function MagicBrojPretraga() {
  const navigate = useNavigate()
  const [uzorak, setUzorak] = useState('*7777')
  const [rezultati, setRezultati] = useState<WildcardMsisdnItem[]>([])
  const [loading, setLoading] = useState(false)

  const trazi = useCallback(async (pattern: string) => {
    if (!pattern.trim()) {
      setRezultati([])
      return
    }
    setLoading(true)
    try {
      const res = await api.wildcardPretraga({ uzorak: pattern, limit: 50 })
      setRezultati(res.rezultati)
    } catch (e) {
      setRezultati([])
      toast.error(e instanceof Error ? e.message : 'Pretraga nije uspjela')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const t = window.setTimeout(() => void trazi(uzorak), 300)
    return () => window.clearTimeout(t)
  }, [uzorak, trazi])

  const odaberi = (id: number) => {
    navigate(`/dodjela?msisdn_id=${id}`)
  }

  return (
    <Card className="border-[#0054A6]/20 bg-gradient-to-br from-[#e6f7fc]/50 to-white p-4 lg:p-6">
      <p className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#0054A6]">
        <Sparkles className="h-4 w-4" />
        Magični broj
      </p>
      <Input
        label="Uzorak (* = bilo koji, ? = jedna znamenka)"
        value={uzorak}
        onChange={(e) => setUzorak(e.target.value)}
        placeholder="npr. *7777"
      />
      <span className="mt-3 flex flex-wrap gap-2">
        {PRESETI.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => setUzorak(p)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:border-[#0054A6] hover:text-[#0054A6]"
          >
            {p}
          </button>
        ))}
      </span>
      {loading && <p className="mt-4 text-sm text-slate-500">Tražim brojeve…</p>}
      {!loading && rezultati.length > 0 && (
        <span className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {rezultati.map((r) => (
            <button
              key={r.id}
              type="button"
              onClick={() => odaberi(r.id)}
              className="rounded-xl border border-slate-100 bg-white p-4 text-left shadow-sm transition hover:border-[#0054A6] hover:shadow-md"
            >
              <p className="font-mono text-lg font-semibold text-[#0054A6]">{r.broj_formatiran}</p>
              <span className="mt-2 flex flex-wrap items-center justify-between gap-2">
                <Badge variant={r.kvaliteta as 'slobodan' | 'zauzet' | 'karantena'}>
                  {r.kvaliteta}
                </Badge>
                <span className="text-sm font-medium text-slate-700">
                  {r.cijena.toLocaleString('hr-HR', { style: 'currency', currency: 'BAM' })}
                </span>
              </span>
              {r.opcina_naziv && (
                <p className="mt-1 text-xs text-slate-500">{r.opcina_naziv}</p>
              )}
            </button>
          ))}
        </span>
      )}
      {!loading && uzorak && rezultati.length === 0 && (
        <p className="mt-4 text-sm text-slate-500">Nema slobodnih brojeva za taj uzorak.</p>
      )}
    </Card>
  )
}
