import { Search } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { toast } from 'sonner'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { MsanUredjajItem, ServisniNalogItem } from '@/types/api'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { EmptyState } from '@/components/ui/EmptyState'

const KOLONE: { status: ServisniNalogItem['status']; label: string }[] = [
  { status: 'otvoren', label: 'Otvoren' },
  { status: 'u_obradi', label: 'U obradi' },
  { status: 'rijesen', label: 'Riješen' },
]

const STATUS_LABEL: Record<ServisniNalogItem['status'], string> = {
  otvoren: 'Otvoren',
  u_obradi: 'U obradi',
  rijesen: 'Riješen',
}

export function ServisniNaloziPage() {
  const { hasUloga } = useAuth()
  const [nalozi, setNalozi] = useState<ServisniNalogItem[]>([])
  const [uredjaji, setUredjaji] = useState<MsanUredjajItem[]>([])
  const [uredjajId, setUredjajId] = useState('')
  const [opis, setOpis] = useState('')
  const [prioritet, setPrioritet] = useState('srednji')
  const [dragId, setDragId] = useState<number | null>(null)
  const [loadingUredjaji, setLoadingUredjaji] = useState(true)
  const [pretragaUredjaja, setPretragaUredjaja] = useState('')
  const [liveMsg, setLiveMsg] = useState('')
  const liveRef = useRef<HTMLDivElement>(null)

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

  useEffect(() => {
    setLoadingUredjaji(true)
    api
      .msanUredjaji()
      .then((lista) => {
        setUredjaji(lista)
        if (lista.length > 0) {
          setUredjajId(String(lista[0].id))
        }
      })
      .catch((e) => toast.error(e instanceof Error ? e.message : 'Uređaji nisu učitani'))
      .finally(() => setLoadingUredjaji(false))
  }, [])

  const premjestiStatus = useCallback(
    async (nalogId: number, noviStatus: ServisniNalogItem['status']) => {
      try {
        await api.servisniNalogAzuriraj(nalogId, { status: noviStatus })
        setLiveMsg(`Nalog #${nalogId} premješten u stupac ${STATUS_LABEL[noviStatus]}.`)
        void load()
      } catch (e) {
        toast.error(e instanceof Error ? e.message : 'Greška')
      } finally {
        setDragId(null)
      }
    },
    [load],
  )

  const onDrop = useCallback(
    (status: ServisniNalogItem['status']) => {
      if (dragId == null) return
      void premjestiStatus(dragId, status)
    },
    [dragId, premjestiStatus],
  )

  if (!hasUloga('admin', 'prodaja')) {
    return <Navigate to="/" replace />
  }

  const kreiraj = async () => {
    if (!uredjajId) {
      toast.error('Odaberi MSAN uređaj.')
      return
    }
    if (!opis.trim()) {
      toast.error('Opis naloga je obavezan.')
      return
    }
    try {
      await api.servisniNalogKreiraj({
        uredjaj_id: Number(uredjajId),
        opis: opis.trim(),
        prioritet,
      })
      setOpis('')
      toast.success('Nalog otvoren.')
      setLiveMsg('Novi servisni nalog otvoren.')
      void load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška')
    }
  }

  const filtriraniUredjaji = useMemo(() => {
    const q = pretragaUredjaja.trim().toLowerCase()
    if (!q) return uredjaji
    return uredjaji.filter(
      (u) =>
        u.naziv.toLowerCase().includes(q) ||
        u.opcina_naziv.toLowerCase().includes(q) ||
        String(u.id).includes(q),
    )
  }, [uredjaji, pretragaUredjaja])

  const uredjajOptions = filtriraniUredjaji.map((u) => ({
    value: String(u.id),
    label: `${u.naziv} · ${u.opcina_naziv} (ID ${u.id})`,
  }))

  useEffect(() => {
    if (uredjajOptions.length === 0) return
    if (!uredjajOptions.some((o) => o.value === uredjajId)) {
      setUredjajId(uredjajOptions[0].value)
    }
  }, [uredjajOptions, uredjajId])

  return (
    <span className="block space-y-6">
      <h1 className="text-2xl font-bold text-[#0054A6]">Servisni nalozi</h1>
      <p className="text-sm text-slate-600">
        Kanban: povucite karticu u drugi stupac ili koristite gumbe „Premjesti u“ (tipkovnica i čitač
        ekrana).
      </p>
      <div
        ref={liveRef}
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {liveMsg}
      </div>
      <Card className="grid gap-3 p-4 md:grid-cols-4">
        {loadingUredjaji ? (
          <p className="text-sm text-slate-500 md:col-span-2">Učitavanje uređaja…</p>
        ) : uredjaji.length === 0 ? (
          <p className="text-sm text-amber-700 md:col-span-2">
            Nema MSAN uređaja u inventaru — pokreni seed ili import.
          </p>
        ) : (
          <span className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">MSAN uređaj</label>
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 px-2.5 py-1.5">
              <Search className="h-3.5 w-3.5 shrink-0 text-slate-400" aria-hidden />
              <input
                type="text"
                value={pretragaUredjaja}
                onChange={(e) => setPretragaUredjaja(e.target.value)}
                placeholder="Pretraži po nazivu, općini ili ID…"
                className="flex-1 bg-transparent text-sm outline-none"
              />
            </div>
            {uredjajOptions.length === 0 ? (
              <p className="text-xs text-slate-500">Nema uređaja za ovaj upit.</p>
            ) : (
              <Select
                value={uredjajId}
                onValueChange={setUredjajId}
                placeholder="Odaberi uređaj"
                options={uredjajOptions}
              />
            )}
          </span>
        )}
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
          <Button
            disabled={loadingUredjaji || !uredjajId || !opis.trim()}
            onClick={() => void kreiraj()}
          >
            Otvori nalog
          </Button>
        </span>
      </Card>
      {!loadingUredjaji && nalozi.length === 0 && (
        <EmptyState
          title="Nema servisnih naloga"
          description="Otvorite nalog odabirom MSAN uređaja i opisa iznad."
        />
      )}
      <span
        className="grid gap-4 lg:grid-cols-3"
        role="region"
        aria-label="Kanban ploča servisnih naloga"
      >
        {KOLONE.map((kol) => (
          <Card
            key={kol.status}
            className="min-h-[200px] p-3"
            onDragOver={(e) => e.preventDefault()}
            onDrop={() => onDrop(kol.status)}
          >
            <h2 className="mb-3 font-semibold text-slate-700">{kol.label}</h2>
            <ul className="space-y-2" role="list">
              {nalozi
                .filter((n) => n.status === kol.status)
                .map((n) => (
                  <li key={n.id}>
                    <article
                      tabIndex={0}
                      draggable
                      onDragStart={() => setDragId(n.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          setDragId(n.id)
                          setLiveMsg(
                            `Nalog #${n.id} odabran za premještaj. Pustite u stupac ili odaberite gumb Premjesti u.`,
                          )
                        }
                      }}
                      aria-label={`Servisni nalog ${n.id}, MSAN ${n.uredjaj_id}, status ${STATUS_LABEL[n.status]}, prioritet ${n.prioritet}`}
                      className="cursor-grab rounded-lg border border-slate-200 bg-white p-3 text-sm shadow-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00A3E0] active:cursor-grabbing dark:bg-slate-800 dark:border-slate-700"
                    >
                      <p className="font-medium">#{n.id} · MSAN {n.uredjaj_id}</p>
                      <p className="mt-1 text-slate-600 dark:text-slate-300">{n.opis}</p>
                      <p className="mt-1 text-xs capitalize text-amber-700">{n.prioritet}</p>
                      <div
                        className="mt-3 flex flex-wrap gap-1 border-t border-slate-100 pt-2 dark:border-slate-700"
                        role="group"
                        aria-label={`Premjesti nalog ${n.id}`}
                      >
                        <span className="w-full text-xs font-medium text-slate-500">Premjesti u:</span>
                        {KOLONE.filter((c) => c.status !== n.status).map((c) => (
                          <Button
                            key={c.status}
                            type="button"
                            variant="outline"
                            size="sm"
                            className="text-xs"
                            onClick={() => void premjestiStatus(n.id, c.status)}
                          >
                            {c.label}
                          </Button>
                        ))}
                      </div>
                    </article>
                  </li>
                ))}
            </ul>
          </Card>
        ))}
      </span>
    </span>
  )
}
