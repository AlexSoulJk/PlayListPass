import { useSearchParams } from 'react-router-dom'
import { AuthCard } from '../../components/AuthCard/AuthCard'
import { AuthShell } from '../../components/AuthShell/AuthShell'
import { RegisterEmailStepForm } from '../../forms/RegisterEmailStepForm/RegisterEmailStepForm'

export function RegisterEmailPage() {
  const [searchParams] = useSearchParams()
  const showUserExistsError = searchParams.get('error') === 'user-exists'

  return (
    <AuthShell>
      <AuthCard>
        <RegisterEmailStepForm showUserExistsError={showUserExistsError} />
      </AuthCard>
    </AuthShell>
  )
}
