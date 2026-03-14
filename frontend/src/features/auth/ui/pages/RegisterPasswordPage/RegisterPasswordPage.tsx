import { Navigate } from 'react-router-dom'
import { useAuth } from '../../../../../app/providers/useAuth'
import { AuthCard } from '../../components/AuthCard/AuthCard'
import { AuthShell } from '../../components/AuthShell/AuthShell'
import { RegisterCredentialsStepForm } from '../../forms/RegisterCredentialsStepForm/RegisterCredentialsStepForm'

export function RegisterPasswordPage() {
  const { registerDraft } = useAuth()

  if (!registerDraft.email) {
    return <Navigate to="/auth/register/email" replace />
  }

  return (
    <AuthShell>
      <AuthCard>
        <RegisterCredentialsStepForm />
      </AuthCard>
    </AuthShell>
  )
}
