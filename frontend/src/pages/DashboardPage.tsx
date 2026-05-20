import { useEffect, useState } from 'react'
import { AlertTriangle, FileSpreadsheet, FileText, Printer } from 'lucide-react'
import { api } from '@/lib/api'
import type { Statistike } from '@/types/api'
import { OpcinaChart } from '@/components/dashboard/OpcinaChart'
import { OpcinaMap } from '@/components/dashboard/OpcinaMap'
import { SjedistaChart } from '@/components/dashboard/SjedistaChart'
import { StatCards } from '@/components/dashboard/StatCards'
import { DodjeleHeatmap } from '@/components/dashboard/DodjeleHeatmap'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { toast } from 'sonner'

const UPOZORENJE_POSTOTAK = 90

function preuzmiBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function DashboardPage() {
  const [data, setData] = useState<Statistike | null>(null)
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState<'excel' | 'pdf' | null>(null)

  useEffect(() => {
    api
      .statistike()
      .then((s) => {
        setData(s)
        if (s.iskoristivost >= UPOZORENJE_POSTOTAK) {
          toast.warning(
            `Visoka iskorištenost brojeva (${s.iskoristivost}%). Preostalo je samo ${s.slobodni} slobodnih brojeva.`,
            { duration: 8000 },
          )
        }
      })
      .catch((e) => toast.error(e instanceof Error ? e.message : 'Greška'))
      .finally(() => setLoading(false))
  }, [])

  const handleExport = async (tip: 'excel' | 'pdf') => {
    setExporting(tip)
    try {
      const blob =
        tip === 'excel' ? await api.izvozStatistikeExcel() : await api.izvozStatistikePdf()
      preuzmiBlob(blob, tip === 'excel' ? 'statistike.xlsx' : 'statistike.pdf')
      toast.success('Izvoz je preuzet')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Izvoz nije uspio')
    } finally {
      setExporting(null)
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-slate-600 animate-fade-in">
          Pregled stanja brojeva HT Eronet sustava za dodjelu.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            loading={exporting === 'excel'}
            onClick={() => void handleExport('excel')}
          >
            <FileSpreadsheet className="h-4 w-4" />
            Excel
          </Button>
          <Button
            variant="outline"
            size="sm"
            loading={exporting === 'pdf'}
            onClick={() => void handleExport('pdf')}
          >
            <FileText className="h-4 w-4" />
            PDF
          </Button>
          <Button variant="outline" size="sm" className="no-print" onClick={() => window.print()}>
            <Printer className="h-4 w-4" />
            Ispiši
          </Button>
        </div>
      </div>

      {data && data.iskoristivost >= UPOZORENJE_POSTOTAK && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="flex items-start gap-3 py-4">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
            <div>
              <p className="font-medium text-amber-900">Upozorenje: visoka iskorištenost</p>
              <p className="text-sm text-amber-800">
                Iskorištenost je {data.iskoristivost}% ({data.slobodni} slobodnih od {data.ukupno}{' '}
                brojeva). Razmotrite dopunu raspona.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <StatCards data={data} loading={loading} />
      <DodjeleHeatmap />
      {data && (
        <>
          <SjedistaChart data={data.po_sjedistima} />
          <Card>
            <CardHeader>
              <CardTitle>Mapa općina</CardTitle>
            </CardHeader>
            <CardContent>
              <OpcinaMap />
            </CardContent>
          </Card>
          <OpcinaChart data={data.po_opcini} />
        </>
      )}
    </div>
  )
}
