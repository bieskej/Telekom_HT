import { Link, NavLink, Outlet } from 'react-router-dom'

import { LogOut, MessageSquare, Phone } from 'lucide-react'

import { usePortalAuth } from '@/context/PortalAuthContext'

import { Button } from '@/components/ui/Button'

import { cn } from '@/lib/utils'



export function PortalLayout() {

  const { kupac, odjava } = usePortalAuth()



  return (

    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">

      <header className="border-b border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">

        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">

          <Link to="/portal/moji-brojevi" className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-xl gradient-primary text-sm font-bold text-white">

              HT

            </div>

            <div>

              <p className="font-bold text-[#0054A6] dark:text-[#00A3E0]">HT Eronet</p>

              <p className="text-xs text-slate-600 dark:text-slate-400">Portal za kupce</p>

            </div>

          </Link>

          <div className="flex items-center gap-3">

            {kupac && (

              <span className="hidden text-sm text-slate-700 dark:text-slate-300 sm:inline">

                {kupac.ime} {kupac.prezime}

              </span>

            )}

            <Button type="button" variant="ghost" size="sm" onClick={odjava}>

              <LogOut className="h-4 w-4" />

              <span className="hidden sm:inline">Odjava</span>

            </Button>

          </div>

        </div>

        <nav className="mx-auto flex max-w-5xl gap-1 border-t border-slate-100 px-4 dark:border-slate-800">

          <NavLink

            to="/portal/moji-brojevi"

            className={({ isActive }) =>

              cn(

                'flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition',

                isActive

                  ? 'border-[#0054A6] text-[#0054A6] dark:border-[#00A3E0] dark:text-[#00A3E0]'

                  : 'border-transparent text-slate-600 hover:text-[#0054A6] dark:text-slate-400 dark:hover:text-[#00A3E0]',

              )

            }

          >

            <Phone className="h-4 w-4" />

            Moji brojevi

          </NavLink>

          <NavLink

            to="/portal/kontakt"

            className={({ isActive }) =>

              cn(

                'flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition',

                isActive

                  ? 'border-[#0054A6] text-[#0054A6] dark:border-[#00A3E0] dark:text-[#00A3E0]'

                  : 'border-transparent text-slate-600 hover:text-[#0054A6] dark:text-slate-400 dark:hover:text-[#00A3E0]',

              )

            }

          >

            <MessageSquare className="h-4 w-4" />

            Kontakt

          </NavLink>

        </nav>

      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">

        <Outlet />

      </main>

    </div>

  )

}


