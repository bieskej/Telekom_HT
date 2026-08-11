import * as DialogPrimitive from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  children: ReactNode
  className?: string
}

export function Dialog({ open, onOpenChange, title, description, children, className }: DialogProps) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out" />
        <DialogPrimitive.Content
          className={cn(
            'fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2',
            'rounded-xl bg-white p-6 shadow-[var(--shadow-modal)] focus:outline-none',
            className,
          )}
        >
          <DialogPrimitive.Title className="text-xl font-semibold text-slate-900">{title}</DialogPrimitive.Title>
          {description && (
            <DialogPrimitive.Description className="mt-1 text-sm text-slate-500">{description}</DialogPrimitive.Description>
          )}
          <DialogPrimitive.Close
            className="absolute right-4 top-4 rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#00A3E0]"
            aria-label="Zatvori dijalog"
          >
            <X className="h-5 w-5" aria-hidden />
          </DialogPrimitive.Close>
          <div className="mt-6">{children}</div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
