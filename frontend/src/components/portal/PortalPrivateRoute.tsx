import { Navigate, Outlet } from 'react-router-dom'
import { portalAuthStorage } from '@/lib/portalAuthStorage'

export function PortalPrivateRoute() {
  if (!portalAuthStorage.isAuthenticated()) {
    return <Navigate to="/portal/prijava" replace />
  }
  return <Outlet />
}
