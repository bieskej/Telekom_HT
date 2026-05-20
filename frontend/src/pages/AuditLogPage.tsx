import { useCallback, useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Download } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { AuditLogItem } from '@/types/api'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Dialog } from '@/components/ui/Dialog'
import { Input } from '@/components/ui/Input'

function bojaAkcije(akcija: string): string {
  if (akcija.includes('dodjela')) return 'bg-emerald-100 text-emerald-800'
  if (akcija.includes('karanten') || akcija.includes('oslobod')) return 'bg-amber-100 text-amber-900'
  if (akcija.includes('brisan') || akcija.includes('odbij')) return 'bg-red-100 text-red-800'
  if (akcija.includes('prijava') || akcija.includes('odjava')) return 'bg-blue-100 text-blue-800'
  return 'bg-slate-100 text-slate-700'
}

export function AuditLogPage() {
  const { hasUloga } = useAuth()
  const [stavke, setStavke] = useState<AuditLogItem[]>([])
  const [entitet, setEntitet] = useState('')
  const [q, setQ] = useState('')
  const [od, setOd] = useState('')
  const [doDat, setDoDat] = useState('')
  const [detalj, setDetalj] = useState<AuditLogItem | null>(null)

  const load = useCallback(async () => {
    try {
      const res = await api.auditLogList({
        entitet: entitet || undefined,
        q: q || undefined,
        od: od || undefined,
        do: doDat || undefined,
      })
      setStavke(res.stavke)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška')
    }
  }, [entitet, q, od, doDat])

  useEffect(() => {
    void load()
  }, [load])

  if (!hasUloga('admin')) {
    return <Navigate to="/" replace />
  }

  const exportCsv = async () => {
    try {
      const blob = await api.auditLogExportCsv({
        entitet: entitet || undefined,
        q: q || undefined,
        od: od || undefined,
        do: doDat || undefined,
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'audit-log.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Export nije uspio')
    }
  }

  return (
    <span className="block space-y-6">
      <span className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-[#0054A6]">Audit log</h1>
        <Button variant="outline" onClick={() => void exportCsv()}>
          <Download className="h-4 w-4" />
          Izvezi CSV
        </Button>
      </span>
      <Card className="grid gap-3 p-4 md:grid-cols-4">
        <Input label="Entitet" value={entitet} onChange={(e) => setEntitet(e.target.value)} />
        <Input label="Pretraga (q)" value={q} onChange={(e) => setQ(e.target.value)} />
        <Input label="Od" type="date" value={od} onChange={(e) => setOd(e.target.value)} />
        <Input label="Do" type="date" value={doDat} onChange={(e) => setDoDat(e.target.value)} />
      </Card>
      <Card className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-slate-50">
              <th className="p-3 text-left">Vrijeme</th>
              <th className="p-3 text-left">Radnik</th>
              <th className="p-3 text-left">Akcija</th>
              <th className="p-3 text-left">Entitet</th>
            </tr>
          </thead>
          <tbody>
            {stavke.map((s) => (
              <tr
                key={s.id}
                className="cursor-pointer border-b hover:bg-slate-50"
                onClick={() => setDetalj(s)}
              >
                <td className="p-3">{s.created_at && new Date(s.created_at).toLocaleString('hr-HR')}</td>
                <td className="p-3">{s.radnik_email ?? '—'}</td>
                <td className="p-3">
                  <span className={`rounded px-2 py-0.5 text-xs font-medium ${bojaAkcije(s.akcija)}`}>
                    {s.akcija}
                  </span>
                </td>
                <td className="p-3">
                  {s.entitet}
                  {s.entitet_id ? ` #${s.entitet_id}` : ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
      <Dialog
        open={!!detalj}
        onOpenChange={(o) => !o && setDetalj(null)}
        title="Detalj zapisa"
        className="max-w-2xl"
      >
        {detalj && (
          <pre className="max-h-96 overflow-auto rounded-lg bg-slate-900 p-4 text-xs text-slate-100">
            {detalj.detalji_json
              ? JSON.stringify(JSON.parse(detalj.detalji_json), null, 2)
              : '{}'}
          </pre>
        )}
      </Dialog>
    </span>
  )
}
