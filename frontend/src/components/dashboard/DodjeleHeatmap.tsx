import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import type { DodjeleHeatmapCelija } from '@/types/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'

const DANI = ['Ned', 'Pon', 'Uto', 'Sri', 'Čet', 'Pet', 'Sub']
const SATI = Array.from({ length: 24 }, (_, i) => i)

function mapKey(dow: number, hour: number) {
  return `${dow}-${hour}`
}

export function DodjeleHeatmap() {
  const [celije, setCelje] = useState<DodjeleHeatmapCelija[]>([])
  const [loading, setLoading] = useState(true)
  const [max, setMax] = useState(1)

  useEffect(() => {
    api
      .dodjeleHeatmap(90)
      .then((res) => {
        setCelje(res.celije)
        setMax(Math.max(1, ...res.celije.map((c) => c.broj)))
      })
      .catch(() => setCelje([]))
      .finally(() => setLoading(false))
  }, [])

  const lookup = new Map(celije.map((c) => [mapKey(c.dow, c.hour), c.broj]))

  return (
    <Card>
      <CardHeader>
        <CardTitle>Dodjele po danu i satu (90 dana)</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-48 w-full" />
        ) : (
          <span className="block overflow-x-auto">
            <table className="w-full min-w-[600px] border-collapse text-xs">
              <thead>
                <tr>
                  <th className="p-1 text-left text-slate-500" />
                  {SATI.map((h) => (
                    <th key={h} className="p-1 font-normal text-slate-500">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {DANI.map((dan, dow) => (
                  <tr key={dan}>
                    <td className="pr-2 font-medium text-slate-600 dark:text-slate-400">{dan}</td>
                    {SATI.map((hour) => {
                      const broj = lookup.get(mapKey(dow, hour)) ?? 0
                      const intenzitet = broj / max
                      return (
                        <td key={hour} className="p-0.5">
                          <span
                            title={`${dan} ${hour}:00 — ${broj} dodjela`}
                            className="block h-6 w-full rounded-sm"
                            style={{
                              backgroundColor: `rgba(0, 84, 166, ${0.08 + intenzitet * 0.92})`,
                            }}
                          />
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </span>
        )}
      </CardContent>
    </Card>
  )
}
