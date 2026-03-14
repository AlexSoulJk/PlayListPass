import type { PropsWithChildren } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../providers/useAuth'

export function ProtectedRoute({ children }: PropsWithChildren) {
  const { status } = useAuth()

  if (status === 'loading') {
    return <div className="app-loading">Checking session...</div>
  }

  if (status !== 'authenticated') {
    return <Navigate to="/auth/login" replace />
  }

  return <>{children}</>
}
