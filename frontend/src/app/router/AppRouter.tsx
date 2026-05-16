import type { PropsWithChildren } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { LandingPage } from '../../features/auth/ui/pages/LandingPage/LandingPage'
import { LoginPage } from '../../features/auth/ui/pages/LoginPage/LoginPage'
import { RegisterPage } from '../../features/auth/ui/pages/RegisterPage/RegisterPage'
import { MainWorkspaceLayout } from '../../features/main/ui/layout/MainWorkspaceLayout/MainWorkspaceLayout'
import { GroupsWorkspacePage } from '../../features/main/ui/pages/GroupsWorkspacePage/GroupsWorkspacePage'
import { PlaylistsWorkspacePage } from '../../features/main/ui/pages/PlaylistsWorkspacePage/PlaylistsWorkspacePage'
import { ProfileWorkspacePage } from '../../features/main/ui/pages/ProfileWorkspacePage/ProfileWorkspacePage'
import { SearchWorkspacePage } from '../../features/main/ui/pages/SearchWorkspacePage/SearchWorkspacePage'
import { ServiceConnectionPage } from '../../features/main/ui/pages/ServiceConnectionPage/ServiceConnectionPage'
import { PlaybackProvider } from '../providers/PlaybackProvider'
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

function LegacyRegisterRedirect() {
  const { search } = useLocation()
  return <Navigate to={`/auth/register${search}`} replace />
}

export function AppRouter() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/welcome"
        element={
          <PublicOnlyRoute>
            <LandingPage />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <PlaybackProvider>
              <MainWorkspaceLayout />
            </PlaybackProvider>
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="groups" replace />} />
        <Route path="service_connection" element={<ServiceConnectionPage />} />
        <Route path="search" element={<SearchWorkspacePage />} />
        <Route path="profile" element={<ProfileWorkspacePage />} />
        <Route path="playlists" element={<PlaylistsWorkspacePage />} />
        <Route path="groups" element={<GroupsWorkspacePage />} />
      </Route>
      <Route
        path="/auth/login"
        element={
          <PublicOnlyRoute>
            <Navigate to="/" replace />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/auth/register"
        element={
          <PublicOnlyRoute>
            <RegisterPage />
          </PublicOnlyRoute>
        }
      />
      <Route path="/auth/register/email" element={<LegacyRegisterRedirect />} />
      <Route path="/auth/register/password" element={<LegacyRegisterRedirect />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
