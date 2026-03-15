import type { ReactNode } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../../../../../app/providers/useAuth'
import styles from './MainWorkspaceLayout.module.css'

type WorkspaceNavItem = {
  id: 'search' | 'profile' | 'playlists' | 'groups'
  label: string
  to: string
  icon: ReactNode
}

const navItems: WorkspaceNavItem[] = [
  {
    id: 'search',
    label: 'Поиск',
    to: '/app/search',
    icon: (
      <svg aria-hidden viewBox="0 0 24 24">
        <circle cx="10.5" cy="10.5" r="6.5" />
        <path d="M16 16L21 21" />
      </svg>
    ),
  },
  {
    id: 'profile',
    label: 'ЛК',
    to: '/app/profile',
    icon: (
      <svg aria-hidden viewBox="0 0 24 24">
        <circle cx="12" cy="7.4" r="3.4" />
        <path d="M5.5 19.5C6.8 16.6 9.2 15.2 12 15.2C14.8 15.2 17.2 16.6 18.5 19.5" />
      </svg>
    ),
  },
  {
    id: 'playlists',
    label: 'Плейлисты',
    to: '/app/playlists',
    icon: (
      <svg aria-hidden viewBox="0 0 24 24">
        <path d="M7 8H17" />
        <path d="M7 12H17" />
        <path d="M7 16H13" />
        <circle cx="17.2" cy="16.2" r="2.3" />
      </svg>
    ),
  },
  {
    id: 'groups',
    label: 'Группы',
    to: '/app/groups',
    icon: (
      <svg aria-hidden viewBox="0 0 24 24">
        <rect x="4" y="5" width="16" height="14" rx="2.2" />
        <path d="M8 9.2H16" />
        <path d="M8 12.5H16" />
        <path d="M8 15.8H13" />
      </svg>
    ),
  },
]

export function MainWorkspaceLayout() {
  const { session, signOut } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    signOut()
    navigate('/', { replace: true })
  }

  return (
    <main className={styles.page}>
      <aside className={styles.sidebar}>
        <div className={styles.sidebarTitleBlock}>
          <p className={styles.sidebarTitle}>Меню</p>
          <p className={styles.sidebarSubtitle}>Разделы приложения</p>
        </div>

        <nav aria-label="Основная навигация" className={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              className={({ isActive }) => (isActive ? `${styles.navItem} ${styles.navItemActive}` : styles.navItem)}
              key={item.id}
              to={item.to}
            >
              <span className={styles.navIcon}>{item.icon}</span>
              <span className={styles.navLabel}>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <button className={styles.logoutButton} onClick={handleLogout} type="button">
          Выйти
        </button>
      </aside>

      <section className={styles.workspace}>
        <header className={styles.header}>
          <div className={styles.headerBrand}>
            <h1 className={styles.headerTitle}>PlayListPass</h1>
            <p className={styles.headerSubtitle}>Объединяйте друзей и управляйте общим музыкальным пространством</p>
          </div>
          <div className={styles.sessionBadge}>{session?.email ?? 'Неизвестный пользователь'}</div>
        </header>

        <div className={styles.content}>
          <Outlet />
        </div>

        <footer className={styles.footer}>
          <p className={styles.footerTitle}>Mock footer</p>
          <p className={styles.footerText}>
            Здесь будет системная информация: статус синхронизации, активная группа, подсказки по управлению.
          </p>
        </footer>
      </section>
    </main>
  )
}
