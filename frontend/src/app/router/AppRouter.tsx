import type { PropsWithChildren } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { LandingPage } from '../../features/auth/ui/pages/LandingPage/LandingPage'
import { LoginPage } from '../../features/auth/ui/pages/LoginPage/LoginPage'
import { ProtectedHomePage } from '../../features/auth/ui/pages/ProtectedHomePage/ProtectedHomePage'
import { RegisterEmailPage } from '../../features/auth/ui/pages/RegisterEmailPage/RegisterEmailPage'
import { RegisterPasswordPage } from '../../features/auth/ui/pages/RegisterPasswordPage/RegisterPasswordPage'
import { useAuth } from '../providers/useAuth'
import { ProtectedRoute } from './ProtectedRoute'

function PublicOnlyRoute({ children }: PropsWithChildren) {
  const { status } = useAuth()

  if (status === 'loading') {
    return <div className="app-loading">Checking session...</div>
  }

  if (status === 'authenticated') {
    return <Navigate to="/app" replace />
  }

  return <>{children}</>
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <ProtectedHomePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/auth/login"
        element={
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/auth/register/email"
        element={
          <PublicOnlyRoute>
            <RegisterEmailPage />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/auth/register/password"
        element={
          <PublicOnlyRoute>
            <RegisterPasswordPage />
          </PublicOnlyRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
