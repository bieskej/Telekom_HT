import { cn } from '@/lib/utils'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <span
      className={cn(
        'inline-block animate-pulse rounded-md bg-slate-200 dark:bg-slate-700',
        className,
      )}
      aria-hidden
    />
  )
}
