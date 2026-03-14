import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { useAuth } from '../../../../../app/providers/useAuth'
import { AuthApiError } from '../../../api/authApi'
import { AuthButtonPrimary } from '../../components/AuthButtonPrimary/AuthButtonPrimary'
import { AuthButtonSecondary } from '../../components/AuthButtonSecondary/AuthButtonSecondary'
import { AuthInlineError } from '../../components/AuthInlineError/AuthInlineError'
import { AuthInput } from '../../components/AuthInput/AuthInput'
import styles from './RegisterCredentialsStepForm.module.css'

const MOCK_LOADER_DURATION_MS = 1500

const registerCredentialsSchema = z
  .object({
    name: z.string().min(2, 'Введите имя'),
    password: z.string().min(8, 'Минимум 8 символов'),
    confirmPassword: z.string().min(8, 'Минимум 8 символов'),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: 'Пароли не совпадают',
    path: ['confirmPassword'],
  })

type RegisterCredentialsValues = z.infer<typeof registerCredentialsSchema>

const wait = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

export function RegisterCredentialsStepForm() {
  const navigate = useNavigate()
  const { registerDraft, setRegisterDraft, registerOnly } = useAuth()
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isMockLoading, setIsMockLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterCredentialsValues>({
    resolver: zodResolver(registerCredentialsSchema),
    defaultValues: {
      name: registerDraft.name,
      password: registerDraft.password,
      confirmPassword: registerDraft.confirmPassword,
    },
  })

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null)
    setRegisterDraft({
      name: values.name,
      password: values.password,
      confirmPassword: values.confirmPassword,
    })

    try {
      await registerOnly({
        email: registerDraft.email,
        name: values.name,
        password: values.password,
      })

      setIsMockLoading(true)
      await wait(MOCK_LOADER_DURATION_MS)
      navigate('/auth/login', { replace: true })
    } catch (error) {
      setIsMockLoading(false)

      if (error instanceof AuthApiError) {
        if (error.code === 'USER_ALREADY_EXISTS') {
          navigate('/auth/register/email?error=user-exists', { replace: true })
          return
        }

        if (error.code === 'NETWORK_ERROR') {
          setSubmitError('Проблема с сетью. Повторите попытку чуть позже.')
          return
        }

        setSubmitError('Не удалось завершить регистрацию. Попробуйте снова.')
        return
      }

      setSubmitError('Не удалось завершить регистрацию. Попробуйте снова.')
    }
  })

  const isBusy = isSubmitting || isMockLoading

  return (
    <form className={styles.form} onSubmit={onSubmit} noValidate aria-busy={isBusy}>
      <fieldset className={styles.fieldset} disabled={isBusy}>
        <div className={styles.inputs}>
          <AuthInput
            {...register('name')}
            id="register-name"
            label="Имя"
            type="text"
            placeholder="Введите имя"
            autoComplete="name"
            errorMessage={errors.name?.message}
          />
          <AuthInput
            {...register('password')}
            id="register-password"
            label="Пароль"
            type="password"
            placeholder="Введите пароль"
            autoComplete="new-password"
            errorMessage={errors.password?.message}
          />
          <AuthInput
            {...register('confirmPassword')}
            id="register-confirm-password"
            label="Повтор пароля"
            type="password"
            placeholder="Повторите пароль"
            autoComplete="new-password"
            errorMessage={errors.confirmPassword?.message}
          />
        </div>

        <div className={styles.buttons}>
          <AuthButtonPrimary disabled={isBusy} type="submit">
            {isBusy ? 'Обработка...' : 'Далее'}
          </AuthButtonPrimary>
          <AuthButtonSecondary onClick={() => navigate('/auth/register/email')} type="button">
            Назад
          </AuthButtonSecondary>
        </div>
      </fieldset>

      {submitError ? <AuthInlineError>{submitError}</AuthInlineError> : null}

      {isMockLoading ? (
        <div className={styles.loadingOverlay} role="status" aria-live="polite">
          <div className={styles.loadingCard}>
            <span className={styles.spinner} aria-hidden />
            <p className={styles.loadingText}>Регистрация завершена. Переходим на страницу входа...</p>
          </div>
        </div>
      ) : null}
    </form>
  )
}
