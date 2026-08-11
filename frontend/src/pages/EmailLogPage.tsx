import { useCallback, useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { Mail, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { EmailLogItem } from '@/types/api'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Dialog } from '@/components/ui/Dialog'
import { Select } from '@/components/ui/Select'

const STATUS_OPTIONS = [
  { value: '', label: 'Svi statusi' },
  { value: 'poslano', label: 'Poslano' },
  { value: 'greska', label: 'Greška' },
  { value: 'nedostaje_smtp', label: 'Nedostaje SMTP' },
]

function statusBadgeVariant(status: string): 'slobodan' | 'zauzet' | 'karantena' {
  if (status === 'poslano') return 'slobodan'
  if (status === 'greska') return 'karantena'
  return 'zauzet'
}

export function EmailLogPage() {
  const { hasUloga } = useAuth()
  const [stavke, setStavke] = useState<EmailLogItem[]>([])
  const [ukupno, setUkupno] = useState(0)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [offset, setOffset] = useState(0)
  const [previewId, setPreviewId] = useState<number | null>(null)
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)
  const [previewOpen, setPreviewOpen] = useState(false)
  const limit = 50

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.emailLogList({
        limit,
        offset,
        status: statusFilter || undefined,
      })
      setStavke(res.stavke)
      setUkupno(res.ukupno)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Greška pri učitavanju loga')
      setStavke([])
      setUkupno(0)
    } finally {
      setLoading(false)
    }
  }, [offset, statusFilter])

  useEffect(() => {
    void load()
  }, [load])

  const openPreview = async (id: number) => {
    try {
      const res = await api.emailLogHtml(id)
      setPreviewId(id)
      setPreviewHtml(res.html)
      setPreviewOpen(true)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Nema HTML pregleda')
    }
  }

  const handleResend = async (id: number, e?: React.MouseEvent) => {
    e?.stopPropagation()
    try {
      await api.emailResend(id)
      toast.success('Email je ponovno poslan.')
      void load()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Ponovno slanje nije uspjelo.')
    }
  }

  if (!hasUloga('admin')) {
    return <Navigate to="/" replace />
  }

  const totalPages = Math.max(1, Math.ceil(ukupno / limit))
  const page = Math.floor(offset / limit) + 1

  return (
    <span className="block space-y-6">
      <span className="flex flex-wrap items-end justify-between gap-4">
        <span>
          <h1 className="text-2xl font-bold text-[#0054A6]">Email log</h1>
          <p className="mt-1 text-sm text-slate-600">
            Pregled poslanih HTML emailova i ponovno slanje (Mailtrap Sandbox u dev okruženju).
          </p>
        </span>
        <Button variant="outline" size="sm" onClick={() => void load()} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Osvježi
        </Button>
      </span>

      <Card className="p-4">
        <Select
          label="Status"
          value={statusFilter}
          onValueChange={(v: string) => {
            setStatusFilter(v)
            setOffset(0)
          }}
          options={STATUS_OPTIONS}
        />
      </Card>

      <Card className="overflow-hidden">
        <span className="block overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="p-4 font-semibold text-slate-700">Primatelj</th>
                <th className="p-4 font-semibold text-slate-700">Predmet</th>
                <th className="p-4 font-semibold text-slate-700">Status</th>
                <th className="p-4 font-semibold text-slate-700">Poslano</th>
                <th className="p-4 font-semibold text-slate-700">Akcija</th>
              </tr>
            </thead>
            <tbody>
              {stavke.length === 0 && !loading && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-500">
                    Nema zapisa u logu.
                  </td>
                </tr>
              )}
              {stavke.map((row) => (
                <tr
                  key={row.id}
                  className="cursor-pointer border-b border-slate-50 transition hover:bg-[#0054A6]/5"
                  onClick={() => row.ima_html && void openPreview(row.id)}
                >
                  <td className="p-4">{row.primatelj}</td>
                  <td className="max-w-xs truncate p-4 text-slate-700" title={row.predmet}>
                    {row.predmet}
                  </td>
                  <td className="p-4">
                    <Badge variant={statusBadgeVariant(row.status)}>{row.status}</Badge>
                  </td>
                  <td className="p-4 text-slate-600">
                    {row.sent_at
                      ? new Date(row.sent_at).toLocaleString('hr-HR')
                      : '—'}
                  </td>
                  <td className="p-4">
                    {row.ima_html && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={(e) => void handleResend(row.id, e)}
                      >
                        <Mail className="h-3.5 w-3.5" />
                        Pošalji ponovno
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </span>
      </Card>

      {ukupno > limit && (
        <span className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={offset === 0}
            onClick={() => setOffset((o) => Math.max(0, o - limit))}
          >
            Prethodna
          </Button>
          <span className="text-sm text-slate-600">
            Stranica {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={offset + limit >= ukupno}
            onClick={() => setOffset((o) => o + limit)}
          >
            Sljedeća
          </Button>
        </span>
      )}

      <Dialog
        open={previewOpen}
        onOpenChange={setPreviewOpen}
        title="Pregled emaila"
        description={previewId ? `Log #${previewId}` : undefined}
        className="max-w-3xl"
      >
        {previewHtml && (
          <iframe
            title="Email preview"
            srcDoc={previewHtml}
            className="h-[min(70vh,520px)] w-full rounded-lg border border-slate-200 bg-white"
            sandbox=""
          />
        )}
        <p className="mt-3 text-xs text-slate-500">
          PDF privitak nije pohranjen u logu — ponovno slanje šalje samo HTML tijelo.
        </p>
      </Dialog>
    </span>
  )
}
