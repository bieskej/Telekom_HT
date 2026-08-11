import { ChevronRight } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { getBreadcrumbs } from '@/lib/breadcrumbRoutes'
import { cn } from '@/lib/utils'

export function Breadcrumbs({ className }: { className?: string }) {
  const { pathname } = useLocation()
  const items = getBreadcrumbs(pathname)

  if (!items?.length) return null

  return (
    <nav aria-label="Putanja stranice" className={cn('text-sm text-slate-500 dark:text-slate-400', className)}>
      <ol className="flex flex-wrap items-center gap-1">
        {items.map((item, i) => {
          const last = i === items.length - 1
          return (
            <li key={`${item.label}-${i}`} className="flex items-center gap-1">
              {i > 0 && <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-400" aria-hidden />}
              {item.to && !last ? (
                <Link
                  to={item.to}
                  className="font-medium text-[#0054A6] hover:underline dark:text-[#00A3E0]"
                >
                  {item.label}
                </Link>
              ) : (
                <span
                  className={cn(last && 'font-medium text-slate-700 dark:text-slate-200')}
                  aria-current={last ? 'page' : undefined}
                >
                  {item.label}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
