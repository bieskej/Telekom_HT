/** Mapa ruta za Breadcrumbs (min. ključne staff rute). */

export interface BreadcrumbItem {
  label: string
  to?: string
}

const ROUTE_LABELS: Record<string, string> = {
  '/': 'Dashboard',
  '/brojevi': 'Brojevi',
  '/korisnici': 'Korisnici',
  '/dodjela': 'Dodjela',
  '/statistika': 'Statistika',
  '/hijerarhija': 'Hijerarhija',
  '/portabilnost': 'Portabilnost',
  '/servisni-nalozi': 'Servisni nalozi',
  '/radnici': 'Radnici',
  '/pomoc': 'Pomoć',
  '/admin/import': 'Import RAK',
  '/admin/email-log': 'Email log',
  '/admin/audit-log': 'Audit log',
  '/admin/eval-priprema': 'Eval priprema',
}

/** Eksplicitni lanac za ugniježđene admin rute. */
const ROUTE_CHAINS: Record<string, BreadcrumbItem[]> = {
  '/admin/import': [
    { label: 'Dashboard', to: '/' },
    { label: 'Admin' },
    { label: 'Import RAK' },
  ],
  '/admin/email-log': [
    { label: 'Dashboard', to: '/' },
    { label: 'Admin' },
    { label: 'Email log' },
  ],
  '/admin/audit-log': [
    { label: 'Dashboard', to: '/' },
    { label: 'Admin' },
    { label: 'Audit log' },
  ],
  '/admin/eval-priprema': [
    { label: 'Dashboard', to: '/' },
    { label: 'Admin' },
    { label: 'Eval priprema' },
  ],
  '/brojevi': [
    { label: 'Dashboard', to: '/' },
    { label: 'Brojevi' },
  ],
  '/dodjela': [
    { label: 'Dashboard', to: '/' },
    { label: 'Dodjela' },
  ],
  '/korisnici': [
    { label: 'Dashboard', to: '/' },
    { label: 'Korisnici' },
  ],
  '/pomoc': [
    { label: 'Dashboard', to: '/' },
    { label: 'Pomoć' },
  ],
}

export function getBreadcrumbs(pathname: string): BreadcrumbItem[] | null {
  if (pathname === '/') return null

  const chain = ROUTE_CHAINS[pathname]
  if (chain) return chain

  const label = ROUTE_LABELS[pathname]
  if (!label) return null

  return [
    { label: 'Dashboard', to: '/' },
    { label },
  ]
}
