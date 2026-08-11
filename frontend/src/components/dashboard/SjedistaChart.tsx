import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { SjedisteStatistika } from '@/types/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'

interface SjedistaChartProps {
  data: SjedisteStatistika[]
}

const BOJA_SLOBODNI = '#16a34a'
const BOJA_ZAUZETI = '#dc2626'

export function SjedistaChart({ data }: SjedistaChartProps) {
  const chartData = data.map((s) => ({
    sjediste: s.sjediste,
    oznaka: s.oznaka,
    slobodni: s.slobodni,
    zauzeti: s.zauzeti,
    karantena: s.karantena,
    ukupno: s.ukupno,
    postotak: s.postotak_zauzetosti,
  }))

  return (
    <Card className="animate-fade-in opacity-0 stagger-2" style={{ animationFillMode: 'forwards' }}>
      <CardHeader>
        <CardTitle>Statistika po sjedištima županija</CardTitle>
        <p className="text-sm text-slate-500">
          Pregled brojeva po sjedištu županije ({data.length} {data.length === 1 ? 'sjedište' : 'sjedišta'}).
        </p>
      </CardHeader>
      <CardContent>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="sjediste"
                tick={{ fontSize: 11, fill: '#64748b' }}
                angle={-35}
                textAnchor="end"
                height={60}
              />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip
                contentStyle={{
                  borderRadius: 12,
                  border: 'none',
                  boxShadow: '0 8px 24px rgba(0,84,166,0.12)',
                }}
                formatter={(value, name) => {
                  const labelMap: Record<string, string> = {
                    slobodni: 'Slobodni',
                    zauzeti: 'Zauzeti',
                    karantena: 'Karantena',
                  }
                  const v = typeof value === 'number' ? value : Number(value ?? 0)
                  return [
                    v.toLocaleString('hr-HR'),
                    labelMap[String(name)] ?? String(name),
                  ]
                }}
                labelFormatter={(label, payload) => {
                  const row = payload?.[0]?.payload as
                    | { oznaka: string; ukupno: number; postotak: number }
                    | undefined
                  if (!row) return label
                  return `${label} (${row.oznaka}) · ukupno ${row.ukupno.toLocaleString(
                    'hr-HR',
                  )} · zauzetost ${row.postotak}%`
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} iconType="square" iconSize={10} />
              <Bar
                dataKey="slobodni"
                stackId="a"
                name="Slobodni"
                fill={BOJA_SLOBODNI}
                radius={[0, 0, 0, 0]}
              >
                {chartData.map((_entry, i) => (
                  <Cell key={`s-${i}`} fill={BOJA_SLOBODNI} />
                ))}
              </Bar>
              <Bar dataKey="zauzeti" stackId="a" name="Zauzeti" fill={BOJA_ZAUZETI}>
                {chartData.map((_entry, i) => (
                  <Cell key={`z-${i}`} fill={BOJA_ZAUZETI} />
                ))}
              </Bar>
              <Bar
                dataKey="karantena"
                stackId="a"
                name="Karantena"
                fill="#f59e0b"
                radius={[8, 8, 0, 0]}
              >
                {chartData.map((_entry, i) => (
                  <Cell key={`k-${i}`} fill="#f59e0b" />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
