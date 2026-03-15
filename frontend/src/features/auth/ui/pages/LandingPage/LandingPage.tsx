import { useNavigate } from 'react-router-dom'
import { AuthButtonPrimary } from '../../components/AuthButtonPrimary/AuthButtonPrimary'
import { AuthButtonSecondary } from '../../components/AuthButtonSecondary/AuthButtonSecondary'
import { AuthCard } from '../../components/AuthCard/AuthCard'
import { AuthShell } from '../../components/AuthShell/AuthShell'
import styles from './LandingPage.module.css'

export function LandingPage() {
  const navigate = useNavigate()

  return (
    <AuthShell>
      <AuthCard className={styles.card}>
        <div className={styles.content}>
          <p className={styles.badge}>PlaylistPass</p>
          <h2 className={styles.lead}>Собирайте общий плейлист за секунды</h2>
          <p className={styles.text}>Войдите в аккаунт или создайте новый профиль, чтобы продолжить.</p>
          <div className={styles.actions}>
            <AuthButtonPrimary className={styles.primaryAction} onClick={() => navigate('/auth/login')} type="button">
              Войти
            </AuthButtonPrimary>
            <AuthButtonSecondary className={styles.secondaryAction} onClick={() => navigate('/auth/register/email')} type="button">
              Регистрация
            </AuthButtonSecondary>
          </div>
        </div>
      </AuthCard>
    </AuthShell>
  )
}
