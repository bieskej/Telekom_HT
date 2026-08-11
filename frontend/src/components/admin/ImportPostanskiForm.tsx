import { useState } from 'react'
import { api } from '@/lib/api'
import type { ImportPostanskiResponse } from '@/types/api'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { toast } from 'sonner'

export function ImportPostanskiForm() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ImportPostanskiResponse | null>(null)

  const handleImport = async () => {
    setLoading(true)
    setResult(null)
    try {
      const res = await api.importPostanskiUredi()
      setResult(res)
      toast.success(`Uvezeno: ${res.novi} novih, ${res.azurirani} ažuriranih`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Import nije uspio')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Poštanski uredi (popis_ureda.pdf)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-slate-600">
          Uvoz iz <code className="rounded bg-slate-100 px-1">popis_ureda.pdf</code> u korijenu projekta.
          Kreira lokacije tipa <strong>postanski_ured</strong> s PB i operaterom (HP/BHP/PS).
        </p>
        <Button type="button" onClick={handleImport} disabled={loading}>
          {loading ? 'Uvoz u tijeku…' : 'Uvezi poštanske urede'}
        </Button>
        {result && (
          <div className="rounded-lg bg-slate-50 p-4 text-sm">
            <p>
              Ukupno: <strong>{result.ukupno}</strong> · Novi: <strong>{result.novi}</strong> · Ažurirani:{' '}
              <strong>{result.azurirani}</strong> · Preskočeni: <strong>{result.preskoceni}</strong>
            </p>
            <p className="mt-2">
              HP: {result.po_operateru.HP ?? 0} · BHP: {result.po_operateru.BHP ?? 0} · PS:{' '}
              {result.po_operateru.PS ?? 0}
            </p>
            {result.needs_review_count > 0 && (
              <p className="mt-2 text-amber-700">
                Za pregled ({result.needs_review_count}): naselja bez mapiranja u master CSV.
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
