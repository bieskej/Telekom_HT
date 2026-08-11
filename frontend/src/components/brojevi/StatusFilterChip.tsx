import { X } from 'lucide-react'
import { FILTER_ALL } from '@/lib/constants'
import { msisdnStatusLabel, msisdnBadgeVariant } from '@/lib/statusUi'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'

interface StatusFilterChipProps {
  status: string
  onClear: () => void
}

/** Prikaz aktivnog status filtera na stranici Brojevi. */
export function StatusFilterChip({ status, onClear }: StatusFilterChipProps) {
  if (!status || status === FILTER_ALL) return null
  const variant = msisdnBadgeVariant(status)
  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      <span className="text-slate-600 dark:text-slate-400">Aktivni filter statusa:</span>
      <Badge variant={variant === 'default' ? 'default' : variant}>
        {msisdnStatusLabel(status)}
      </Badge>
      <Button type="button" variant="ghost" size="sm" onClick={onClear} aria-label="Ukloni filter statusa">
        <X className="h-4 w-4" />
        Ukloni
      </Button>
    </div>
  )
}
