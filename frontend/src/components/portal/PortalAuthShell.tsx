import type { ReactNode } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'

interface PortalAuthShellProps {
  title: string
  subtitle?: string
  children: ReactNode
  footer?: ReactNode
  showLogo?: boolean
}

/** Zajednički okvir prijave/registracije portala (usklađen sa staff PrijavaPage). */
export function PortalAuthShell({
  title,
  subtitle,
  children,
  footer,
  showLogo = true,
}: PortalAuthShellProps) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-[#0054A6]/10 via-white to-[#00A3E0]/10 dark:from-[#0054A6]/25 dark:via-slate-950 dark:to-slate-900" />
      <Card className="w-full max-w-md animate-fade-in shadow-[var(--shadow-modal)]">
        <CardHeader className="text-center">
          {showLogo && (
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl gradient-primary text-xl font-bold text-white shadow-lg">
              HT
            </div>
          )}
          <CardTitle className="text-2xl text-[#0054A6] dark:text-[#00A3E0]">{title}</CardTitle>
          {subtitle && (
            <p className="text-sm text-slate-600 dark:text-slate-400">{subtitle}</p>
          )}
        </CardHeader>
        <CardContent>
          {children}
          {footer}
        </CardContent>
      </Card>
    </div>
  )
}
