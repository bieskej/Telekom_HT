import { ArrowRight, Hash, MapPin, Radio, Server } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Badge } from '@/components/ui/Badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { buttonVariants } from '@/components/ui/Button'
import { cn } from '@/lib/utils'
import type {
  HijerarhijaCvorDetalj,
  HijerarhijaCvorTip,
} from '@/types/api'

interface HijerarhijaDetaljProps {
  detalj: HijerarhijaCvorDetalj | null
  loading: boolean
}

const IKONE: Record<HijerarhijaCvorTip, typeof MapPin> = {
  zupanija: MapPin,
  opcina: MapPin,
  lokacija: MapPin,
  uredjaj: Server,
}

const STATUS_STIL: Record<string, string> = {
  slobodan: 'bg-emerald-100 text-emerald-700',
  zauzet: 'bg-red-100 text-red-700',
  karantena: 'bg-amber-100 text-amber-700',
  rezerviran: 'bg-blue-100 text-blue-700',
  portano: 'bg-slate-200 text-slate-700',
}

const KVALITETA_STIL: Record<string, string> = {
  silver: 'bg-slate-100 text-slate-600',
  gold: 'bg-yellow-100 text-yellow-800',
  platinum: 'bg-indigo-100 text-indigo-700',
  diamond: 'bg-purple-100 text-purple-700',
}

function MetricCard({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color: string
}) {
  return (
    <div className="rounded-xl border border-slate-100 bg-white p-3 shadow-sm">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
        {label}
      </p>
      <p className={cn('mt-0.5 text-2xl font-bold', color)}>
        {value.toLocaleString('hr-HR')}
      </p>
    </div>
  )
}

export function HijerarhijaDetalj({ detalj, loading }: HijerarhijaDetaljProps) {
  if (loading) {
    return (
      <Card>
        <CardContent className="p-8">
          <p className="text-sm text-slate-400">Učitavanje detalja…</p>
        </CardContent>
      </Card>
    )
  }

  if (!detalj) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center p-12 text-center">
          <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full bg-[#0054A6]/10">
            <Radio className="h-8 w-8 text-[#0054A6]" />
          </div>
          <p className="text-base font-medium text-slate-700">
            Odaberi čvor s lijeve strane
          </p>
          <p className="mt-1 max-w-sm text-sm text-slate-500">
            Klikni županiju, općinu, lokaciju ili MSAN uređaj u stablu lijevo da
            vidiš detalje i uzorke MSISDN-a.
          </p>
        </CardContent>
      </Card>
    )
  }

  const Ikona = IKONE[detalj.tip]
  const postotak =
    detalj.metrike.ukupno > 0
      ? Math.round((detalj.metrike.zauzeti / detalj.metrike.ukupno) * 100)
      : 0
  const brojeviHref = detalj.filter_param
    ? `/brojevi?${detalj.filter_param.kljuc}=${encodeURIComponent(detalj.filter_param.vrijednost)}`
    : '/brojevi'

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3 py-4">
          <div className="flex items-start gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#0054A6]/10 text-[#0054A6]">
              <Ikona className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-lg">{detalj.naslov}</CardTitle>
              <p className="mt-0.5 text-xs text-slate-500">{detalj.opis}</p>
            </div>
          </div>
          <Link
            to={brojeviHref}
            className={cn(buttonVariants({ variant: 'primary', size: 'md' }))}
          >
            Otvori u Brojevi
            <ArrowRight className="ml-1.5 h-4 w-4" />
          </Link>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetricCard
              label="Ukupno"
              value={detalj.metrike.ukupno}
              color="text-slate-800"
            />
            <MetricCard
              label="Slobodni"
              value={detalj.metrike.slobodni}
              color="text-emerald-600"
            />
            <MetricCard
              label="Zauzeti"
              value={detalj.metrike.zauzeti}
              color="text-red-600"
            />
            <MetricCard
              label="Karantena"
              value={detalj.metrike.karantena}
              color="text-amber-600"
            />
          </div>

          <div className="mt-4">
            <div className="mb-1.5 flex items-center justify-between text-xs text-slate-500">
              <span>Iskoristivost (zauzeti / ukupno)</span>
              <span className="font-semibold">{postotak}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className={cn(
                  'h-full rounded-full transition-all',
                  postotak > 90
                    ? 'bg-red-500'
                    : postotak > 50
                      ? 'bg-amber-500'
                      : 'bg-emerald-500',
                )}
                style={{ width: `${Math.min(postotak, 100)}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between py-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Hash className="h-4 w-4 text-[#0054A6]" />
            Uzorak MSISDN brojeva ({detalj.brojevi_uzorak.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {detalj.brojevi_uzorak.length === 0 ? (
            <p className="text-sm text-slate-400">Nema brojeva za prikaz.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-slate-100">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-3 py-2">Broj</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Kvaliteta</th>
                  </tr>
                </thead>
                <tbody>
                  {detalj.brojevi_uzorak.map((b) => (
                    <tr
                      key={b.id}
                      className="border-t border-slate-50 hover:bg-slate-50/60"
                    >
                      <td className="px-3 py-2 font-mono text-[#0054A6]">
                        {b.broj}
                      </td>
                      <td className="px-3 py-2">
                        <Badge
                          className={cn(
                            STATUS_STIL[b.status] ?? 'bg-slate-100 text-slate-600',
                          )}
                        >
                          {b.status}
                        </Badge>
                      </td>
                      <td className="px-3 py-2">
                        <Badge
                          className={cn(
                            KVALITETA_STIL[b.kvaliteta] ??
                              'bg-slate-100 text-slate-600',
                          )}
                        >
                          {b.kvaliteta}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
