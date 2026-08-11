import type { LucideIcon } from 'lucide-react'
import { Inbox } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { buttonVariants } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

export interface EmptyStateAction {
  label: string
  to: string
}

export interface EmptyStateProps {
  title: string
  description?: string
  icon?: LucideIcon
  action?: EmptyStateAction
  className?: string
}

export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  action,
  className,
}: EmptyStateProps) {
  return (
    <Card
      className={cn('flex flex-col items-center px-6 py-10 text-center', className)}
      role="status"
    >
      <Icon className="mb-3 h-10 w-10 text-slate-300 dark:text-slate-600" aria-hidden />
      <p className="text-base font-semibold text-slate-700 dark:text-slate-200">{title}</p>
      {description && (
        <p className="mt-2 max-w-md text-sm text-slate-500 dark:text-slate-400">{description}</p>
      )}
      {action && (
        <Link to={action.to} className={cn(buttonVariants({ variant: 'primary', size: 'md' }), 'mt-5')}>
          {action.label}
        </Link>
      )}
    </Card>
  )
}
