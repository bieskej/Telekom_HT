import { useCallback, useRef, useState } from 'react'
import { FileSpreadsheet, Upload } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '@/lib/api'
import type { ImportRakResponse } from '@/types/api'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'

export function ImportRakForm() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ImportRakResponse | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const pickFile = (f: File | null) => {
    if (!f) return
    const name = f.name.toLowerCase()
    if (!name.endsWith('.xlsx') && !name.endsWith('.csv')) {
      toast.error('Dozvoljeni formati: .xlsx, .csv')
      return
    }
    setFile(f)
    setResult(null)
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files[0]
    pickFile(f ?? null)
  }, [])

  const handleImport = async () => {
    if (!file) {
      toast.error('Odaberite datoteku')
      return
    }
    setLoading(true)
    try {
      const res = await api.importRak(file)
      setResult(res)
      toast.success(`Uvezeno ${res.novi_brojevi} novih brojeva`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Import nije uspio')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileSpreadsheet className="h-5 w-5 text-[#0054A6]" />
          Import RAK blokova
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <p className="text-sm text-slate-600">
          Učitajte Excel ili CSV datoteku s HT Eronet blokovima (format kao službeni RAK izvještaj).
          Uvozi se samo redovi s operatorom HT d.d./d.o.o. Mostar.
        </p>

        <div
          role="button"
          tabIndex={0}
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-12 transition-colors ${
            dragOver ? 'border-[#00A3E0] bg-[#e6f7fc]' : 'border-slate-200 bg-slate-50 hover:border-[#0054A6]/40'
          }`}
        >
          <Upload className="h-10 w-10 text-[#0054A6]/60" />
          <div className="text-center">
            <p className="font-medium text-slate-700">
              {file ? file.name : 'Povucite datoteku ovdje ili kliknite za odabir'}
            </p>
            <p className="mt-1 text-xs text-slate-500">.xlsx, .csv</p>
          </div>
        </div>

        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.csv"
          className="hidden"
          onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
        />

        <Button loading={loading} onClick={() => void handleImport()} disabled={!file}>
          Uvezi
        </Button>

        {result && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
            <p>
              <strong>Novi rasponi:</strong> {result.novi_rasponi}
            </p>
            <p>
              <strong>Novi brojevi:</strong> {result.novi_brojevi}
            </p>
            <p>
              <strong>Preskočeni (duplikati):</strong> {result.preskoceni}
            </p>
            {result.obradeno_blokova != null && (
              <p>
                <strong>Obradeno blokova:</strong> {result.obradeno_blokova}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
