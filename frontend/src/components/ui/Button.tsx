import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import { Loader2 } from 'lucide-react'
import type { ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-[10px] font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#00A3E0] focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-slate-900 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary:
          'bg-[#0054A6] text-white shadow-md hover:bg-[#003d78] hover:shadow-lg active:scale-[0.98]',
        accent:
          'bg-[#00A3E0] text-white shadow-md hover:bg-[#0088bb] active:scale-[0.98]',
        outline:
          'border-2 border-[#0054A6]/20 bg-white text-[#0054A6] hover:bg-[#e6f2fa] dark:border-slate-600 dark:bg-slate-900 dark:text-[#00A3E0] dark:hover:bg-slate-800',
        ghost:
          'text-[#0054A6] hover:bg-[#0054A6]/8 dark:text-[#00A3E0] dark:hover:bg-slate-800',
        danger: 'bg-red-600 text-white hover:bg-red-700',
      },
      size: {
        sm: 'h-9 px-3 text-sm',
        md: 'h-11 px-5 text-sm',
        lg: 'h-12 px-6 text-base',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
}

export function Button({
  className,
  variant,
  size,
  asChild = false,
  loading,
  children,
  disabled,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : 'button'
  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </Comp>
  )
}
