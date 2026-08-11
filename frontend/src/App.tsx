import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { Toaster } from 'sonner'
import { PrivateRoute } from '@/components/auth/PrivateRoute'
import { PortalPrivateRoute } from '@/components/portal/PortalPrivateRoute'
import { PortalLayout } from '@/components/portal/PortalLayout'
import { Layout } from '@/components/layout/Layout'
import { AuthProvider } from '@/context/AuthContext'
import { PortalAuthProvider } from '@/context/PortalAuthContext'
import { BrojeviPage } from '@/pages/BrojeviPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { DodjelaPage } from '@/pages/DodjelaPage'
import { PrijavaPage } from '@/pages/PrijavaPage'
import { HijerarhijaPage } from '@/pages/HijerarhijaPage'
import { ImportPage } from '@/pages/ImportPage'
import { EmailLogPage } from '@/pages/EmailLogPage'
import { PortabilnostPage } from '@/pages/PortabilnostPage'
import { ServisniNaloziPage } from '@/pages/ServisniNaloziPage'
import { AuditLogPage } from '@/pages/AuditLogPage'
import { KorisniciPage } from '@/pages/KorisniciPage'
import { RadniciPage } from '@/pages/RadniciPage'
import { StatistikaPage } from '@/pages/StatistikaPage'
import { PortalPrijavaPage } from '@/pages/portal/PortalPrijavaPage'
import { PortalRegistracijaPage } from '@/pages/portal/PortalRegistracijaPage'
import { PortalMojiBrojeviPage } from '@/pages/portal/PortalMojiBrojeviPage'
import { PortalKontaktPage } from '@/pages/portal/PortalKontaktPage'
import { HelpPage } from '@/pages/HelpPage'
import { EvalPripremaPage } from '@/pages/admin/EvalPripremaPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/prijava" element={<PrijavaPage />} />
          <Route
            path="/portal"
            element={
              <PortalAuthProvider>
                <Outlet />
              </PortalAuthProvider>
            }
          >
            <Route index element={<Navigate to="/portal/moji-brojevi" replace />} />
            <Route path="prijava" element={<PortalPrijavaPage />} />
            <Route path="registracija" element={<PortalRegistracijaPage />} />
            <Route element={<PortalPrivateRoute />}>
              <Route element={<PortalLayout />}>
                <Route path="moji-brojevi" element={<PortalMojiBrojeviPage />} />
                <Route path="kontakt" element={<PortalKontaktPage />} />
              </Route>
            </Route>
          </Route>
          <Route element={<PrivateRoute />}>
            <Route element={<Layout />}>
              <Route index element={<DashboardPage />} />
              <Route path="brojevi" element={<BrojeviPage />} />
              <Route path="korisnici" element={<KorisniciPage />} />
              <Route path="dodjela" element={<DodjelaPage />} />
              <Route path="statistika" element={<StatistikaPage />} />
              <Route path="hijerarhija" element={<HijerarhijaPage />} />
              <Route path="radnici" element={<RadniciPage />} />
              <Route path="admin/import" element={<ImportPage />} />
              <Route path="admin/email-log" element={<EmailLogPage />} />
              <Route path="admin/audit-log" element={<AuditLogPage />} />
              <Route path="admin/eval-priprema" element={<EvalPripremaPage />} />
              <Route path="portabilnost" element={<PortabilnostPage />} />
              <Route path="pomoc" element={<HelpPage />} />
              <Route path="servisni-nalozi" element={<ServisniNaloziPage />} />
              <Route
                path="servisni_nalozi"
                element={<Navigate to="/servisni-nalozi" replace />}
              />
            </Route>
          </Route>
          <Route path="/login" element={<Navigate to="/prijava" replace />} />
          <Route path="/portal/login" element={<Navigate to="/portal/prijava" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster
          position="top-right"
          richColors
          toastOptions={{
            classNames: {
              toast:
                'rounded-xl shadow-lg border border-slate-200 bg-white text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100',
              title: 'text-slate-900 dark:text-slate-100',
              description: 'text-slate-600 dark:text-slate-400',
            },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  )
}
