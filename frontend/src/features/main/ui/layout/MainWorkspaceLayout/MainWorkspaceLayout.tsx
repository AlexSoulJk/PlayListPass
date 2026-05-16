import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../../../../../app/providers/useAuth'
import { usePlayback } from '../../../../../app/providers/usePlayback'
import { AppSidebar } from '../../../../../shared/ui/AppSidebar/AppSidebar'
import { sidebarSectionItems } from '../../../../../shared/ui/AppSidebar/sidebarItems'
import { GlobalPlayer } from '../../../../../shared/ui/GlobalPlayer/GlobalPlayer'
import styles from './MainWorkspaceLayout.module.css'

export function MainWorkspaceLayout() {
  const { session, signOut } = useAuth()
  const { currentTrack, isHidden } = usePlayback()
  const navigate = useNavigate()

  const handleLogout = () => {
    signOut()
    navigate('/', { replace: true })
  }

  return (
    <main className={styles.page}>
      <AppSidebar items={sidebarSectionItems} onLogout={handleLogout} />

      <section className={styles.workspace}>
        <header className={styles.header}>
          <div className={styles.headerBrand}>
            <h1 className={styles.headerTitle}>PlaylistPass</h1>
            <p className={styles.headerSubtitle}>
              Объединяйте друзей и управляйте общим музыкальным пространством
            </p>
          </div>
          <div className={styles.sessionBadge}>{session?.email ?? 'Неизвестный пользователь'}</div>
        </header>

        <div className={styles.content}>
          <Outlet />
        </div>

        {currentTrack && !isHidden ? <GlobalPlayer /> : null}
      </section>
    </main>
  )
}
