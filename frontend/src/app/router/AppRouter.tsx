import type { PropsWithChildren } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { LandingPage } from '../../features/auth/ui/pages/LandingPage/LandingPage'
import { LoginPage } from '../../features/auth/ui/pages/LoginPage/LoginPage'
import { RegisterEmailPage } from '../../features/auth/ui/pages/RegisterEmailPage/RegisterEmailPage'
import { RegisterPasswordPage } from '../../features/auth/ui/pages/RegisterPasswordPage/RegisterPasswordPage'
import { MainWorkspaceLayout } from '../../features/main/ui/layout/MainWorkspaceLayout/MainWorkspaceLayout'
import { GroupsWorkspacePage } from '../../features/main/ui/pages/GroupsWorkspacePage/GroupsWorkspacePage'
import { PlaylistsWorkspacePage } from '../../features/main/ui/pages/PlaylistsWorkspacePage/PlaylistsWorkspacePage'
import { ProfileWorkspacePage } from '../../features/main/ui/pages/ProfileWorkspacePage/ProfileWorkspacePage'
import { SearchWorkspacePage } from '../../features/main/ui/pages/SearchWorkspacePage/SearchWorkspacePage'
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
            <MainWorkspaceLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="groups" replace />} />
        <Route path="search" element={<SearchWorkspacePage />} />
        <Route path="profile" element={<ProfileWorkspacePage />} />
        <Route path="playlists" element={<PlaylistsWorkspacePage />} />
        <Route path="groups" element={<GroupsWorkspacePage />} />
      </Route>
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
