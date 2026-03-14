import { AuthCard } from '../../components/AuthCard/AuthCard'
import { AuthShell } from '../../components/AuthShell/AuthShell'
import { LoginForm } from '../../forms/LoginForm/LoginForm'

export function LoginPage() {
  return (
    <AuthShell>
      <AuthCard>
        <LoginForm />
      </AuthCard>
    </AuthShell>
  )
}
