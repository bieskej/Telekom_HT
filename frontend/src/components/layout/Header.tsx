import { LogOut, Moon, Sun, User } from 'lucide-react'
import { useDarkMode } from '@/hooks/useDarkMode'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/context/AuthContext'
import { MobileMenuButton } from './Sidebar'

interface HeaderProps {
  onMenuClick: () => void
  title: string
}

export function Header({ onMenuClick, title }: HeaderProps) {
  const { radnik, odjava } = useAuth()
  const { dark, toggle } = useDarkMode()

  return (
    <header className="sticky top-0 z-30 border-b border-slate-100/80 bg-white/90 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/90 no-print">
      <div className="flex h-16 items-center justify-between gap-4 px-4 lg:px-8">
        <div className="flex items-center gap-3">
          <MobileMenuButton onClick={onMenuClick} />
          <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100 lg:text-xl">{title}</h1>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={toggle} aria-label="Tamni način">
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
          <div className="hidden items-center gap-3 rounded-xl bg-[#F5F5F5] px-4 py-2 dark:bg-slate-800 sm:flex">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#0054A6]/10 text-[#0054A6]">
              <User className="h-4 w-4" />
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                {radnik?.ime} {radnik?.prezime}
              </p>
              <p className="text-xs capitalize text-slate-500">{radnik?.uloga ?? ''}</p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={odjava}>
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Odjava</span>
          </Button>
        </div>
      </div>
    </header>
  )
}
