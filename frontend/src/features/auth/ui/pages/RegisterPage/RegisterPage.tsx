import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { AppSidebar, type AppSidebarItem } from '../../../../../shared/ui/AppSidebar/AppSidebar'
import { sidebarSectionItems } from '../../../../../shared/ui/AppSidebar/sidebarItems'
import { AuthCard } from '../../components/AuthCard/AuthCard'
import { ServicesFooterLogos } from '../../components/ServicesFooterLogos/ServicesFooterLogos'
import { RegisterForm } from '../../forms/RegisterForm/RegisterForm'
import styles from './RegisterPage.module.css'

export function RegisterPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const showUserExistsFromQuery = searchParams.get('error') === 'user-exists'

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
            <AuthCard className={styles.registerCard}>
              <h2 className={styles.cardTitle}>Регистрация</h2>
              <RegisterForm showUserExistsFromQuery={showUserExistsFromQuery} />
            </AuthCard>
            <p className={styles.loginText}>
              У вас уже есть аккаунт?{' '}
              <Link className={styles.loginLink} to="/">
                Вход
              </Link>
            </p>
          </div>
        </section>

        <ServicesFooterLogos />
      </section>
    </main>
  )
}
