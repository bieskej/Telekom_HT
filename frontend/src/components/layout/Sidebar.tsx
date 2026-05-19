import { BarChart3, GitBranch, Hash, LayoutDashboard, Mail, Menu, PhoneCall, Radio, Upload, UserCircle, Users, Wrench, X } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { cn } from '@/lib/utils'
import { SidebarExtras } from '@/components/layout/SidebarExtras'

const baseNav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/brojevi', label: 'Brojevi', icon: Hash },
  { to: '/korisnici', label: 'Korisnici', icon: UserCircle },
  { to: '/dodjela', label: 'Dodjela', icon: PhoneCall, uloge: ['admin', 'prodaja'] as const },
  { to: '/portabilnost', label: 'Portabilnost', icon: Radio, uloge: ['admin', 'prodaja'] as const },
  { to: '/servisni-nalozi', label: 'Servisni nalozi', icon: Wrench, uloge: ['admin'] as const },
  { to: '/statistika', label: 'Statistika', icon: BarChart3 },
  { to: '/hijerarhija', label: 'Hijerarhija', icon: GitBranch },
  { to: '/radnici', label: 'Radnici', icon: Users, uloge: ['admin'] as const },
  { to: '/admin/import', label: 'Import RAK', icon: Upload, uloge: ['admin'] as const },
  { to: '/admin/email-log', label: 'Email log', icon: Mail, uloge: ['admin'] as const },
]

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const { hasUloga } = useAuth()
  const navItems = baseNav.filter((item) => !item.uloge || item.uloge.some((u) => hasUloga(u)))

  return (
    <>
      <div
        className={cn(
          'fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm transition-opacity lg:hidden',
          open ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
        onClick={onClose}
        aria-hidden={!open}
      />
      <aside
        className={cn(
          'fixed left-0 top-0 z-50 flex h-full w-72 flex-col bg-white shadow-xl transition-transform duration-300 ease-out lg:static lg:translate-x-0 lg:shadow-none',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl gradient-primary text-sm font-bold text-white">
              HT
            </div>
            <div>
              <p className="font-bold text-[#0054A6]">HT Eronet</p>
              <p className="text-xs text-slate-500">Dodjela brojeva</p>
            </div>
          </div>
          <button type="button" className="rounded-lg p-2 lg:hidden hover:bg-slate-100" onClick={onClose}>
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex flex-1 flex-col overflow-hidden p-4">
          <span className="space-y-1 overflow-y-auto">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                onClick={onClose}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200',
                    isActive
                      ? 'bg-[#0054A6] text-white shadow-md'
                      : 'text-slate-600 hover:bg-[#0054A6]/8 hover:text-[#0054A6]',
                  )
                }
              >
                <Icon className="h-5 w-5" />
                {label}
              </NavLink>
            ))}
            <SidebarExtras onNavigate={onClose} />
          </span>
        </nav>
        <div className="border-t border-slate-100 p-4 text-xs text-slate-400">© 2026 HT Eronet</div>
      </aside>
    </>
  )
}

export function MobileMenuButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-xl border border-slate-200 bg-white p-2.5 shadow-sm transition hover:bg-slate-50 lg:hidden"
      aria-label="Izbornik"
    >
      <Menu className="h-5 w-5 text-[#0054A6]" />
    </button>
  )
}
