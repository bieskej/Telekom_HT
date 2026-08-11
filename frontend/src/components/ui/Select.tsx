import * as SelectPrimitive from '@radix-ui/react-select'

import { Check, ChevronDown } from 'lucide-react'

import { useId } from 'react'

import { FILTER_ALL } from '@/lib/constants'

import { cn } from '@/lib/utils'



export interface SelectOption {

  value: string

  label: string

}



interface SelectProps {

  label?: string

  value: string

  onValueChange: (v: string) => void

  placeholder?: string

  options: SelectOption[]

  className?: string

  id?: string

  error?: string

}



export function Select({

  label,

  value,

  onValueChange,

  placeholder,

  options,

  className,

  id,

  error,

}: SelectProps) {

  const uid = useId()

  const selectId = id ?? (label ? `select-${uid}` : undefined)

  const errorId = error && selectId ? `${selectId}-error` : undefined

  const safeValue = value === '' ? FILTER_ALL : value

  const safeOptions = options.map((o) => ({

    ...o,

    value: o.value === '' ? FILTER_ALL : o.value,

  }))



  return (

    <div className={cn('space-y-1.5', className)}>

      {label && selectId && (

        <label htmlFor={selectId} className="text-sm font-medium text-slate-700 dark:text-slate-300">

          {label}

        </label>

      )}

      {label && !selectId && (

        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{label}</span>

      )}

      <SelectPrimitive.Root value={safeValue} onValueChange={onValueChange}>

        <SelectPrimitive.Trigger

          id={selectId}

          aria-invalid={error ? true : undefined}

          aria-describedby={errorId}

          className={cn(

            'flex h-11 w-full items-center justify-between rounded-[10px] border border-slate-200 bg-white px-4 text-sm text-slate-900 focus:border-[#00A3E0] focus:outline-none focus:ring-2 focus:ring-[#00A3E0]/25 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100',

            error && 'border-red-500 focus:border-red-500 focus:ring-red-200/80 dark:border-red-500',

          )}

        >

          <SelectPrimitive.Value placeholder={placeholder ?? 'Odaberi...'} />

          <SelectPrimitive.Icon>

            <ChevronDown className="h-4 w-4 text-slate-500" />

          </SelectPrimitive.Icon>

        </SelectPrimitive.Trigger>

        <SelectPrimitive.Portal>

          <SelectPrimitive.Content

            position="popper"

            sideOffset={4}

            className="z-50 max-h-[min(var(--radix-select-content-available-height,280px),280px)] overflow-hidden rounded-xl border border-slate-100 bg-white shadow-[var(--shadow-modal)] dark:border-slate-700 dark:bg-slate-900"

          >

            <SelectPrimitive.Viewport className="max-h-[280px] overflow-y-auto p-1">

              {safeOptions.map((opt) => (

                <SelectPrimitive.Item

                  key={opt.value}

                  value={opt.value}

                  className="relative flex cursor-pointer select-none items-center rounded-lg py-2.5 pl-8 pr-3 text-sm text-slate-800 outline-none hover:bg-[#0054A6]/8 data-[highlighted]:bg-[#0054A6]/10 dark:text-slate-100 dark:data-[highlighted]:bg-[#0054A6]/25"

                >

                  <SelectPrimitive.ItemIndicator className="absolute left-2">

                    <Check className="h-4 w-4 text-[#0054A6]" />

                  </SelectPrimitive.ItemIndicator>

                  <SelectPrimitive.ItemText>{opt.label}</SelectPrimitive.ItemText>

                </SelectPrimitive.Item>

              ))}

            </SelectPrimitive.Viewport>

          </SelectPrimitive.Content>

        </SelectPrimitive.Portal>

      </SelectPrimitive.Root>

      {error && (

        <p id={errorId} role="alert" className="text-xs text-red-600 dark:text-red-400">

          {error}

        </p>

      )}

    </div>

  )

}


