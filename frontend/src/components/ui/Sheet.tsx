import * as DialogPrimitive from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface SheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  children: ReactNode
  className?: string
  /** Širina panela, default 28rem. */
  widthClass?: string
}

/**
 * Desni slide-over panel (Sheet) baziran na Radix Dialog.
 * Animacija: translate-x s desne strane.
 */
export function Sheet({
  open,
  onOpenChange,
  title,
  description,
  children,
  className,
  widthClass = 'w-[28rem]',
}: SheetProps) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay
          className={cn(
            'fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm transition-opacity duration-200',
            'data-[state=closed]:opacity-0 data-[state=open]:opacity-100',
          )}
        />
        <DialogPrimitive.Content
          className={cn(
            'fixed right-0 top-0 z-50 flex h-full flex-col bg-white shadow-2xl',
            'transition-transform duration-300 ease-out',
            'data-[state=closed]:translate-x-full data-[state=open]:translate-x-0',
            'focus:outline-none',
            widthClass,
            className,
          )}
        >
          <div className="flex items-start justify-between border-b border-slate-100 px-5 py-4">
            <div>
              <DialogPrimitive.Title className="text-base font-semibold text-[#0054A6]">
                {title}
              </DialogPrimitive.Title>
              {description && (
                <DialogPrimitive.Description className="mt-0.5 text-xs text-slate-500">
                  {description}
                </DialogPrimitive.Description>
              )}
            </div>
            <DialogPrimitive.Close
              aria-label="Zatvori panel"
              className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            >
              <X className="h-5 w-5" />
            </DialogPrimitive.Close>
          </div>
          <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
