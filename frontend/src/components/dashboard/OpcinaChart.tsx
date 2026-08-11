import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { OpcinaStatistika } from '@/types/api'
import { bojaZaZauzetost, ZAUZETOST_LEGENDA } from '@/lib/statusUi'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'

interface OpcinaChartProps {
  data: OpcinaStatistika[]
}

export function OpcinaChart({ data }: OpcinaChartProps) {
  const chartData = data.map((o) => ({
    naziv: o.naziv.length > 12 ? `${o.naziv.slice(0, 10)}…` : o.naziv,
    puniNaziv: o.naziv,
    postotak: o.postotak_zauzetosti,
    slobodni: o.slobodni,
  }))

  return (
    <Card className="animate-fade-in opacity-0 stagger-3" style={{ animationFillMode: 'forwards' }}>
      <CardHeader className="space-y-3">
        <CardTitle>Iskoristivost po općinama</CardTitle>
        <div className="flex flex-wrap gap-4 text-xs text-slate-600" role="list" aria-label="Legenda zauzetosti">
          {ZAUZETOST_LEGENDA.map((item) => (
            <span key={item.label} className="flex items-center gap-1.5" role="listitem">
              <span
                className="inline-block h-3 w-3 rounded"
                style={{ backgroundColor: item.boja }}
                aria-hidden
              />
              {item.label}
            </span>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="naziv"
                tick={{ fontSize: 11, fill: '#64748b' }}
                angle={-35}
                textAnchor="end"
                height={60}
              />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} unit="%" domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  borderRadius: 12,
                  border: 'none',
                  boxShadow: '0 8px 24px rgba(0,84,166,0.12)',
                }}
                formatter={(value) => [`${value ?? 0}%`, 'Zauzetost']}
                labelFormatter={(_, payload) =>
                  (payload?.[0]?.payload as { puniNaziv?: string })?.puniNaziv ?? ''
                }
              />
              <Bar dataKey="postotak" radius={[8, 8, 0, 0]} maxBarSize={48}>
                {chartData.map((entry) => (
                  <Cell key={entry.puniNaziv} fill={bojaZaZauzetost(entry.postotak)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
