import { useNavigate, Link } from 'react-router-dom'
import { ThemeToggle } from '../../../../../shared/ui/ThemeToggle/ThemeToggle'
import { AuthCard } from '../../components/AuthCard/AuthCard'
import { ServicesFooterLogos } from '../../components/ServicesFooterLogos/ServicesFooterLogos'
import { LoginForm } from '../../forms/LoginForm/LoginForm'
import styles from './LoginPage.module.css'

const guestNavItems = ['Группы', 'Поиск', 'Личный кабинет', 'Плейлисты']

export function LoginPage() {
  const navigate = useNavigate()

  const handleProtectedNavigationAttempt = () => {
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
          {guestNavItems.map((item) => (
            <button className={styles.navItem} key={item} onClick={handleProtectedNavigationAttempt} type="button">
              <span className={styles.navLabel}>{item}</span>
            </button>
          ))}
        </nav>

        <div className={styles.themeToggleWrap}>
          <ThemeToggle />
        </div>
      </aside>

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
