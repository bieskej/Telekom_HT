import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { Statistike } from '@/types/api'
import { OpcinaChart } from '@/components/dashboard/OpcinaChart'
import { StatCards } from '@/components/dashboard/StatCards'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { toast } from 'sonner'

export function StatistikaPage() {
  const [data, setData] = useState<Statistike | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .statistike()
      .then(setData)
      .catch((e) => toast.error(e instanceof Error ? e.message : 'Greška'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-8">
      <StatCards data={data} loading={loading} />
      {data && <OpcinaChart data={data.po_opcini} />}
      {data && (
        <Card>
          <CardHeader>
            <CardTitle>Detalji po općinama</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-slate-500">
                    <th className="pb-3 pr-4">Općina</th>
                    <th className="pb-3 pr-4">Ukupno</th>
                    <th className="pb-3 pr-4">Slobodni</th>
                    <th className="pb-3">Zauzetost %</th>
                  </tr>
                </thead>
                <tbody>
                  {data.po_opcini.map((o) => (
                    <tr key={o.naziv} className="border-b border-slate-50">
                      <td className="py-3 font-medium">{o.naziv}</td>
                      <td className="py-3">{o.ukupno}</td>
                      <td className="py-3 text-emerald-600">{o.slobodni}</td>
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <div className="h-2 flex-1 max-w-[120px] rounded-full bg-slate-100">
                            <div
                              className="h-2 rounded-full bg-[#0054A6]"
                              style={{ width: `${o.postotak_zauzetosti}%` }}
                            />
                          </div>
                          <span>{o.postotak_zauzetosti}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
