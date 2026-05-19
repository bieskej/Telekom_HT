import { useCallback, useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { toast } from 'sonner'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { ServisniNalogItem } from '@/types/api'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'

const KOLONE: { status: ServisniNalogItem['status']; label: string }[] = [
  { status: 'otvoren', label: 'Otvoren' },
  { status: 'u_obradi', label: 'U obradi' },
  { status: 'rijesen', label: 'Riješen' },
]

export function ServisniNaloziPage() {
  const { hasUloga } = useAuth()
  const [nalozi, setNalozi] = useState<ServisniNalogItem[]>([])
  const [uredjajId, setUredjajId] = useState('1')
  const [opis, setOpis] = useState('')
  const [prioritet, setPrioritet] = useState('srednji')
  const [dragId, setDragId] = useState<number | null>(null)

  const load = useCallback(async () => {
    try {
      setNalozi(await api.servisniNaloziLista())
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška')
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  if (!hasUloga('admin', 'prodaja')) {
    return <Navigate to="/" replace />
  }

  const kreiraj = async () => {
    try {
      await api.servisniNalogKreiraj({
        uredjaj_id: Number(uredjajId),
        opis,
        prioritet,
      })
      setOpis('')
      toast.success('Nalog otvoren.')
      void load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška')
    }
  }

  const onDrop = async (status: string) => {
    if (dragId == null) return
    try {
      await api.servisniNalogAzuriraj(dragId, { status })
      void load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška')
    }
    setDragId(null)
  }

  return (
    <span className="block space-y-6">
      <h1 className="text-2xl font-bold text-[#0054A6]">Servisni nalozi</h1>
      <Card className="grid gap-3 p-4 md:grid-cols-4">
        <Input label="Uređaj ID" value={uredjajId} onChange={(e) => setUredjajId(e.target.value)} />
        <Input label="Opis" value={opis} onChange={(e) => setOpis(e.target.value)} />
        <Select
          label="Prioritet"
          value={prioritet}
          onValueChange={setPrioritet}
          options={[
            { value: 'niski', label: 'Niski' },
            { value: 'srednji', label: 'Srednji' },
            { value: 'kritican', label: 'Kritičan' },
          ]}
        />
        <span className="flex items-end">
          <Button onClick={() => void kreiraj()}>Otvori nalog</Button>
        </span>
      </Card>
      <span className="grid gap-4 lg:grid-cols-3">
        {KOLONE.map((kol) => (
          <Card
            key={kol.status}
            className="min-h-[200px] p-3"
            onDragOver={(e) => e.preventDefault()}
            onDrop={() => void onDrop(kol.status)}
          >
            <p className="mb-3 font-semibold text-slate-700">{kol.label}</p>
            <span className="space-y-2">
              {nalozi
                .filter((n) => n.status === kol.status)
                .map((n) => (
                  <div
                    key={n.id}
                    draggable
                    onDragStart={() => setDragId(n.id)}
                    className="cursor-grab rounded-lg border border-slate-200 bg-white p-3 text-sm shadow-sm active:cursor-grabbing"
                  >
                    <p className="font-medium">#{n.id} · MSAN {n.uredjaj_id}</p>
                    <p className="mt-1 text-slate-600">{n.opis}</p>
                    <p className="mt-1 text-xs capitalize text-amber-700">{n.prioritet}</p>
                  </div>
                ))}
            </span>
          </Card>
        ))}
      </span>
    </span>
  )
}
