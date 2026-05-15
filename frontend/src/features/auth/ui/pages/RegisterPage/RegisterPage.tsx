import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ThemeToggle } from '../../../../../shared/ui/ThemeToggle/ThemeToggle'
import { AuthCard } from '../../components/AuthCard/AuthCard'
import { ServicesFooterLogos } from '../../components/ServicesFooterLogos/ServicesFooterLogos'
import { RegisterForm } from '../../forms/RegisterForm/RegisterForm'
import styles from './RegisterPage.module.css'

const guestNavItems = ['Группы', 'Поиск', 'Личный кабинет', 'Плейлисты']

export function RegisterPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const showUserExistsFromQuery = searchParams.get('error') === 'user-exists'

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

