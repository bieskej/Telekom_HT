import { useState } from 'react'

import { Outlet, useLocation } from 'react-router-dom'

import { Breadcrumbs } from './Breadcrumbs'

import { DemoBanner } from './DemoBanner'

import { Header } from './Header'

import { Sidebar } from './Sidebar'



const titles: Record<string, string> = {

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



export function Layout() {

  const [sidebarOpen, setSidebarOpen] = useState(false)

  const { pathname } = useLocation()

  const title = titles[pathname] ?? 'HT Eronet'



  return (

    <div className="flex min-h-screen">

      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex min-h-screen flex-1 flex-col lg:ml-0">

        <DemoBanner />

        <Header title={title} onMenuClick={() => setSidebarOpen(true)} />

        <main className="flex-1 p-4 lg:p-8">

          <Breadcrumbs className="mb-4" />

          <Outlet />

        </main>

      </div>

    </div>

  )

}


