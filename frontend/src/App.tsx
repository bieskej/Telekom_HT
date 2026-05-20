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
              <Route path="portabilnost" element={<PortabilnostPage />} />
              <Route path="servisni-nalozi" element={<ServisniNaloziPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        <Toaster
          position="top-right"
          richColors
          toastOptions={{
            classNames: { toast: 'rounded-xl shadow-lg border border-slate-100' },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  )
}
