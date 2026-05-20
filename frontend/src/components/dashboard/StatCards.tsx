import { Activity, Hash, Lock, Phone } from 'lucide-react'
import type { Statistike } from '@/types/api'
import { Card } from '@/components/ui/Card'
import { AnimatedNumber } from '@/components/ui/AnimatedNumber'
import { Skeleton } from '@/components/ui/Skeleton'
import { cn } from '@/lib/utils'

const cards = [
  {
    key: 'iskoristivost' as const,
    label: 'Iskoristivost',
    icon: Activity,
    gradient: 'from-[#0054A6] to-[#00A3E0]',
    suffix: '%',
    border: 'border-l-[#00A3E0]',
  },
  {
    key: 'ukupno' as const,
    label: 'Ukupno brojeva',
    icon: Hash,
    gradient: 'from-slate-700 to-slate-500',
    suffix: '',
    border: 'border-l-slate-400',
  },
  {
    key: 'slobodni' as const,
    label: 'Slobodni',
    icon: Phone,
    gradient: 'from-emerald-600 to-emerald-400',
    suffix: '',
    border: 'border-l-emerald-500',
  },
  {
    key: 'zauzeti' as const,
    label: 'Zauzeti',
    icon: Lock,
    gradient: 'from-[#0054A6] to-[#003d78]',
    suffix: '',
    border: 'border-l-[#0054A6]',
  },
]

interface StatCardsProps {
  data: Statistike | null
  loading?: boolean
}

export function StatCards({ data, loading }: StatCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((c, i) => {
        const Icon = c.icon
        const value =
          c.key === 'iskoristivost'
            ? data?.iskoristivost ?? 0
            : data?.[c.key] ?? 0
        return (
          <Card
            key={c.key}
            className={cn(
              'card-hover border-accent-left overflow-hidden animate-fade-in opacity-0',
              c.border,
              `stagger-${i + 1}`,
            )}
            style={{ animationFillMode: 'forwards' }}
          >
            <div className="flex items-start justify-between p-6">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{c.label}</p>
                <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-slate-100">
                  {loading ? (
                    <Skeleton className="inline-block h-9 w-20" />
                  ) : (
                    <AnimatedNumber
                      value={value}
                      suffix={c.suffix}
                      decimals={c.key === 'iskoristivost' ? 1 : 0}
                    />
                  )}
                </p>
              </div>
              <div
                className={cn(
                  'flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-md',
                  c.gradient,
                )}
              >
                <Icon className="h-6 w-6" />
              </div>
            </div>
          </Card>
        )
      })}
    </div>
  )
}
