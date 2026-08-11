import { AlertTriangle } from 'lucide-react'

const showDemoBanner =
  import.meta.env.DEV || import.meta.env.VITE_DEMO_BANNER === 'true'

export function DemoBanner() {
  if (!showDemoBanner) return null

  return (
    <div
      role="status"
      className="flex items-center justify-center gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2 text-center text-sm font-medium text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/40 dark:text-amber-200 no-print"
    >
      <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
      Demo okruženje — podaci nisu produkcijski
    </div>
  )
}
