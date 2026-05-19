import { useCallback, useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { toast } from 'sonner'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { PortabilnostItem } from '@/types/api'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'

const STATUSI = ['zahtjev', 'u_obradi', 'realiziran', 'odbijen'] as const

export function PortabilnostPage() {
  const { hasUloga } = useAuth()
  const [stavke, setStavke] = useState<PortabilnostItem[]>([])
  const [tip, setTip] = useState('port_in')
  const [broj, setBroj] = useState('')
  const [izvor, setIzvor] = useState('')
  const [cilj, setCilj] = useState('HT d.d. Mostar')

  const load = useCallback(async () => {
    try {
      setStavke(await api.portabilnostLista())
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
      await api.portabilnostKreiraj({
        tip,
        broj: tip === 'port_in' ? broj : undefined,
        izvor_op: izvor,
        ciljni_op: cilj,
      })
      toast.success('Zahtjev kreiran.')
      void load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška')
    }
  }

  const promijeniStatus = async (id: number, status: string) => {
    try {
      await api.portabilnostAzuriraj(id, { status })
      void load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška')
    }
  }

  return (
    <span className="block space-y-6">
      <h1 className="text-2xl font-bold text-[#0054A6]">Portabilnost</h1>
      <Card className="p-4 space-y-3">
        <Select
          label="Tip"
          value={tip}
          onValueChange={setTip}
          options={[
            { value: 'port_in', label: 'Port-in' },
            { value: 'port_out', label: 'Port-out' },
          ]}
        />
        {tip === 'port_in' && (
          <Input label="Broj" value={broj} onChange={(e) => setBroj(e.target.value)} />
        )}
        <Input label="Izvorni operater" value={izvor} onChange={(e) => setIzvor(e.target.value)} />
        <Input label="Ciljni operater" value={cilj} onChange={(e) => setCilj(e.target.value)} />
        <Button onClick={() => void kreiraj()}>Novi zahtjev</Button>
      </Card>
      <Card className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-slate-50">
              <th className="p-3 text-left">ID</th>
              <th className="p-3 text-left">Tip</th>
              <th className="p-3 text-left">Broj</th>
              <th className="p-3 text-left">Status</th>
              <th className="p-3 text-left">Operateri</th>
              <th className="p-3 text-left">Akcija</th>
            </tr>
          </thead>
          <tbody>
            {stavke.map((s) => (
              <tr key={s.id} className="border-b">
                <td className="p-3">{s.id}</td>
                <td className="p-3">{s.tip}</td>
                <td className="p-3 font-mono">{s.broj ?? '—'}</td>
                <td className="p-3">
                  <Badge variant="zauzet">{s.status}</Badge>
                </td>
                <td className="p-3 text-xs">
                  {s.izvor_op} → {s.ciljni_op}
                </td>
                <td className="p-3">
                  <Select
                    value={s.status}
                    onValueChange={(v) => void promijeniStatus(s.id, v)}
                    options={STATUSI.map((st) => ({ value: st, label: st }))}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </span>
  )
}
