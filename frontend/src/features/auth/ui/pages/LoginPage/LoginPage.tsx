import { Link, useNavigate } from 'react-router-dom'
import { AppSidebar, type AppSidebarItem } from '../../../../../shared/ui/AppSidebar/AppSidebar'
import { sidebarSectionItems } from '../../../../../shared/ui/AppSidebar/sidebarItems'
import { AuthCard } from '../../components/AuthCard/AuthCard'
import { ServicesFooterLogos } from '../../components/ServicesFooterLogos/ServicesFooterLogos'
import { LoginForm } from '../../forms/LoginForm/LoginForm'
import styles from './LoginPage.module.css'

export function LoginPage() {
  const navigate = useNavigate()

  const handleProtectedNavigationAttempt = () => {
    navigate('/', { replace: true })
  }

  const sidebarItems: AppSidebarItem[] = sidebarSectionItems.map((item) => ({
    id: item.id,
    label: item.label,
    icon: item.icon,
    onClick: handleProtectedNavigationAttempt,
    active: item.id === 'groups',
  }))

  return (
    <main className={styles.page}>
      <AppSidebar items={sidebarItems} />

      <section className={styles.workspace}>
        <header className={styles.header}>
          <h1 className={styles.headerTitle}>PlaylistPass</h1>
          <p className={styles.headerSubtitle}>сервис для создания совместных музыкальных плейлистов</p>
        </header>

        <section className={styles.mainContainer}>
          <div className={styles.formArea}>
            <AuthCard className={styles.loginCard}>
              <h2 className={styles.cardTitle}>Вход</h2>
              <LoginForm />
            </AuthCard>
            <p className={styles.registerText}>
              У вас еще нет аккаунта?{' '}
              <Link className={styles.registerLink} to="/auth/register">
                Регистрация
              </Link>
            </p>
          </div>
        </section>

        <ServicesFooterLogos />
      </section>
    </main>
  )
}
