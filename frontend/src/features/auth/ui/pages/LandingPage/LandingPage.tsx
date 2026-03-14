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
      <AuthCard>
        <div className={styles.content}>
          <p className={styles.lead}>Welcome to PlaylistPass</p>
          <p className={styles.text}>Choose an action to continue to login or registration.</p>
          <div className={styles.actions}>
            <AuthButtonPrimary onClick={() => navigate('/auth/login')} type="button">
              Login
            </AuthButtonPrimary>
            <AuthButtonSecondary onClick={() => navigate('/auth/register/email')} type="button">
              Register
            </AuthButtonSecondary>
          </div>
        </div>
      </AuthCard>
    </AuthShell>
  )
}
