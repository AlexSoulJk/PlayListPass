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

      await wait(MOCK_LOADER_DURATION_MS)
      navigate('/auth/login', { replace: true })
    } catch (error) {

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

  const isBusy = isSubmitting

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

        <section aria-label="Шаг пользовательских кредов" className={styles.credentialsMock}>
          <p className={styles.credentialsMockTitle}>Шаг пользовательских кредов (mock)</p>
          <p className={styles.credentialsMockText}>
            Здесь будет экран подключения и ввода данных музыкального сервиса после загрузки финальных артефактов.
          </p>
          <div className={styles.credentialsMockPreview} aria-hidden>
            <span className={styles.credentialsMockDot}>Y</span>
            <span className={styles.credentialsMockLine} />
            <span className={styles.credentialsMockDot}>S</span>
            <span className={styles.credentialsMockLine} />
            <span className={styles.credentialsMockDot}>YT</span>
          </div>
        </section>

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
    </form>
  )
}
