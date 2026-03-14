import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { useAuth } from '../../../../../app/providers/useAuth'
import { AuthButtonPrimary } from '../../components/AuthButtonPrimary/AuthButtonPrimary'
import { AuthButtonSecondary } from '../../components/AuthButtonSecondary/AuthButtonSecondary'
import { AuthInput } from '../../components/AuthInput/AuthInput'
import styles from './RegisterEmailStepForm.module.css'

type RegisterEmailStepFormProps = {
  showUserExistsError?: boolean
}

const registerEmailSchema = z.object({
  email: z.string().email('Введите корректную почту'),
})

type RegisterEmailFormValues = z.infer<typeof registerEmailSchema>

export function RegisterEmailStepForm({ showUserExistsError = false }: RegisterEmailStepFormProps) {
  const navigate = useNavigate()
  const { registerDraft, setRegisterDraft } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterEmailFormValues>({
    resolver: zodResolver(registerEmailSchema),
    defaultValues: {
      email: registerDraft.email,
    },
  })

  const onSubmit = handleSubmit((values) => {
    setRegisterDraft({ email: values.email })
    navigate('/auth/register/password')
  })

  const emailError =
    errors.email?.message ?? (showUserExistsError ? 'Пользователь уже зарегистрирован' : undefined)

  return (
    <form className={styles.form} onSubmit={onSubmit} noValidate>
      <div className={styles.inputs}>
        <AuthInput
          {...register('email')}
          id="register-email"
          label="Почта"
          type="email"
          placeholder="Введите почту или номер телефона"
          autoComplete="email"
          errorMessage={emailError}
        />
      </div>

      <div className={styles.buttons}>
        <AuthButtonPrimary disabled={isSubmitting} type="submit">
          Далее
        </AuthButtonPrimary>
        <AuthButtonSecondary onClick={() => navigate('/')} type="button">
          Назад
        </AuthButtonSecondary>
      </div>
    </form>
  )
}
