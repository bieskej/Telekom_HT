import { Navigate, Outlet } from 'react-router-dom'
import { authStorage } from '@/lib/authStorage'

export function PrivateRoute() {
  if (!authStorage.isAuthenticated()) {
    return <Navigate to="/prijava" replace />
  }
  const radnik = authStorage.getRadnik()
  if (radnik?.uloga === 'kupac') {
    return <Navigate to="/portal/moji-brojevi" replace />
  }
  return <Outlet />
}
