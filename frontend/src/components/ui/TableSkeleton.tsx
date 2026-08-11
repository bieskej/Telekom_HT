import { Card } from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'
import { cn } from '@/lib/utils'

interface TableSkeletonProps {
  rows?: number
  className?: string
}

/** Skeleton tablice (Brojevi, Portabilnost). */
export function TableSkeleton({ rows = 6, className }: TableSkeletonProps) {
  return (
    <Card className={cn('overflow-hidden p-4', className)}>
      <Skeleton className="mb-4 h-10 w-full" aria-hidden />
      <span className="block space-y-3" aria-busy="true" aria-label="Učitavanje tablice">
        {Array.from({ length: rows }, (_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </span>
    </Card>
  )
}

interface CardGridSkeletonProps {
  count?: number
  className?: string
}

/** Skeleton mreže kartica (Korisnici). */
export function CardGridSkeleton({ count = 6, className }: CardGridSkeletonProps) {
  return (
    <span
      className={cn('grid gap-3 sm:grid-cols-2 xl:grid-cols-3', className)}
      aria-busy="true"
      aria-label="Učitavanje korisnika"
    >
      {Array.from({ length: count }, (_, i) => (
        <Skeleton key={i} className="h-36 w-full rounded-xl" />
      ))}
    </span>
  )
}
