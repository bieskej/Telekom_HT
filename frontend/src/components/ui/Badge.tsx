import { cva, type VariantProps } from 'class-variance-authority'

import type { HTMLAttributes } from 'react'

import { MSISDN_STATUS, msisdnBadgeClass, msisdnStatusLabel, type MsisdnStatus } from '@/lib/statusUi'

import { cn } from '@/lib/utils'



const badgeVariants = cva(

  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',

  {

    variants: {

      variant: {

        slobodan: MSISDN_STATUS.slobodan.badge,

        zauzet: MSISDN_STATUS.zauzet.badge,

        karantena: MSISDN_STATUS.karantena.badge,

        portano: MSISDN_STATUS.portano.badge,

        default: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',

      },

    },

    defaultVariants: { variant: 'default' },

  },

)



export type BadgeVariant = VariantProps<typeof badgeVariants>['variant']



export function Badge({

  className,

  variant,

  children,

  ...props

}: HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {

  return (

    <span className={cn(badgeVariants({ variant }), className)} {...props}>

      {children}

    </span>

  )

}



/** Badge MSISDN statusa s automatskim labelom i bojom. */

export function MsisdnStatusBadge({

  status,

  className,

}: {

  status: string

  className?: string

}) {

  const v = status in MSISDN_STATUS ? (status as MsisdnStatus) : 'default'

  return (

    <Badge variant={v} className={className}>

      {msisdnStatusLabel(status)}

    </Badge>

  )

}



/** Klasa iz statusUi za nepoznate varijante (npr. portabilnost). */

export function BadgeFromStatus({

  status,

  className,

}: {

  status: string

  className?: string

}) {

  return (

    <span

      className={cn(

        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',

        msisdnBadgeClass(status),

        className,

      )}

    >

      {msisdnStatusLabel(status)}

    </span>

  )

}


