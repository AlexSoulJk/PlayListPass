import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../../../app/providers/useAuth'
import styles from './ProtectedHomePage.module.css'

export function ProtectedHomePage() {
  const { session, signOut } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    signOut()
    navigate('/', { replace: true })
  }

  return (
    <main className={styles.page}>
      <section className={styles.panel}>
        <h1 className={styles.title}>Вы авторизованы</h1>
        <p className={styles.subtitle}>Текущий пользователь: {session?.email ?? 'unknown'}</p>
        <p className={styles.note}>Это мок защищенной страницы.</p>
        <button className={styles.logoutButton} onClick={handleLogout} type="button">
          Выйти
        </button>
      </section>
    </main>
  )
}
