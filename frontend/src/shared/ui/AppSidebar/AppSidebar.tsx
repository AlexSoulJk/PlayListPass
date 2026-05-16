import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { ThemeToggle } from '../ThemeToggle/ThemeToggle'
import styles from './AppSidebar.module.css'

export type AppSidebarItem =
  | {
      id: string
      label: string
      icon?: ReactNode
      to: string
    }
  | {
      id: string
      label: string
      icon?: ReactNode
      onClick: () => void
      active?: boolean
      disabled?: boolean
    }

type AppSidebarProps = {
  items: AppSidebarItem[]
  onLogout?: () => void
  logoutLabel?: string
  title?: string
  subtitle?: string
  navAriaLabel?: string
}

const navItemClassName = (isActive: boolean): string => {
  return isActive ? `${styles.navItem} ${styles.navItemActive}` : styles.navItem
}

export function AppSidebar({
  items,
  onLogout,
  logoutLabel = 'Выйти',
  title = 'Меню',
  subtitle = 'Разделы приложения',
  navAriaLabel = 'Основная навигация',
}: AppSidebarProps) {
  return (
    <aside className={styles.root}>
      <div className={styles.titleBlock}>
        <p className={styles.title}>{title}</p>
        <p className={styles.subtitle}>{subtitle}</p>
      </div>

      <nav aria-label={navAriaLabel} className={styles.nav}>
        {items.map((item) => {
          if ('to' in item) {
            return (
              <NavLink className={({ isActive }) => navItemClassName(isActive)} key={item.id} to={item.to}>
                {item.icon ? <span className={styles.navIcon}>{item.icon}</span> : null}
                <span className={styles.navLabel}>{item.label}</span>
              </NavLink>
            )
          }

          const className = navItemClassName(Boolean(item.active))
          return (
            <button
              className={className}
              disabled={item.disabled}
              key={item.id}
              onClick={item.onClick}
              type="button"
            >
              {item.icon ? <span className={styles.navIcon}>{item.icon}</span> : null}
              <span className={styles.navLabel}>{item.label}</span>
            </button>
          )
        })}
      </nav>

      <div className={styles.bottom}>
        <ThemeToggle />
        {onLogout ? (
          <button className={styles.logoutButton} onClick={onLogout} type="button">
            {logoutLabel}
          </button>
        ) : null}
      </div>
    </aside>
  )
}
