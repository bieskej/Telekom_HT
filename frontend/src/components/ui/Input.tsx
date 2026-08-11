import { useId, type InputHTMLAttributes } from 'react'

import { cn } from '@/lib/utils'



export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {

  label?: string

  error?: string

}



export function Input({ className, label, error, id, ...props }: InputProps) {

  const uid = useId()

  const inputId = id ?? (label ? `input-${uid}` : undefined)

  const errorId = error && inputId ? `${inputId}-error` : undefined



  return (

    <div className="space-y-1.5">

      {label && inputId && (

        <label htmlFor={inputId} className="text-sm font-medium text-slate-700 dark:text-slate-300">

          {label}

        </label>

      )}

      {label && !inputId && (

        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{label}</span>

      )}

      <input

        id={inputId}

        aria-invalid={error ? true : undefined}

        aria-describedby={errorId}

        className={cn(

          'flex h-11 w-full rounded-[10px] border border-slate-200 bg-white px-4 text-sm transition-colors dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100',

          'placeholder:text-slate-400 focus:border-[#00A3E0] focus:outline-none focus:ring-2 focus:ring-[#00A3E0]/25',

          error && 'border-red-500 focus:border-red-500 focus:ring-red-200/80 dark:border-red-500',

          className,

        )}

        {...props}

      />

      {error && (

        <p id={errorId} role="alert" className="text-xs text-red-600 dark:text-red-400">

          {error}

        </p>

      )}

    </div>

  )

}


