import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { useAuth } from '../../../../../app/providers/useAuth'
import { AuthApiError } from '../../../api/authApi'
import { markServiceConnectionPending } from '../../../serviceConnectionAccess'
import { AuthButtonPrimary } from '../../components/AuthButtonPrimary/AuthButtonPrimary'
import { AuthErrorBanner } from '../../components/AuthErrorBanner/AuthErrorBanner'
import { AuthInlineError } from '../../components/AuthInlineError/AuthInlineError'
import { AuthInput } from '../../components/AuthInput/AuthInput'
import styles from './RegisterForm.module.css'

type RegisterFormProps = {
  showUserExistsFromQuery?: boolean
}

const registerSchema = z
  .object({
    email: z.string().email('Введите корректную почту'),
    name: z.string().min(2, 'Введите имя'),
    password: z.string().min(8, 'Минимум 8 символов'),
    confirmPassword: z.string().min(8, 'Минимум 8 символов'),
  })
  .refine((values) => values.password === values.confirmPassword, {
    message: 'Пароли не совпадают',
    path: ['confirmPassword'],
  })

type RegisterFormValues = z.infer<typeof registerSchema>

const OPEN_SERVICE_WINDOW_FEATURES = 'noopener,noreferrer'

export function RegisterForm({ showUserExistsFromQuery = false }: RegisterFormProps) {
  const navigate = useNavigate()
  const { registerOnly, signIn } = useAuth()
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [userExistsError, setUserExistsError] = useState(showUserExistsFromQuery)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      name: '',
      password: '',
      confirmPassword: '',
    },
  })

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null)
    setUserExistsError(false)

    try {
      await registerOnly({
        email: values.email,
        name: values.name,
        password: values.password,
      })

      await signIn({
        email: values.email,
        password: values.password,
      })

      markServiceConnectionPending()
      window.open('/app/service_connection', '_blank', OPEN_SERVICE_WINDOW_FEATURES)
      navigate('/app', { replace: true })
    } catch (error) {
      if (error instanceof AuthApiError) {
        if (error.code === 'USER_ALREADY_EXISTS') {
          setUserExistsError(true)
          return
        }

        if (error.code === 'NETWORK_ERROR') {
          setSubmitError('Проблема с сетью. Повторите попытку чуть позже.')
          return
        }
      }

      setSubmitError('Не удалось завершить регистрацию. Попробуйте снова.')
    }
  })

  const isBusy = isSubmitting
  const errorToneClassName = userExistsError ? styles.fieldErrorTone : undefined

  return (
    <form className={styles.form} onSubmit={onSubmit} noValidate aria-busy={isBusy}>
      <fieldset className={styles.fieldset} disabled={isBusy}>
        {userExistsError ? <AuthErrorBanner>Пользователь уже зарегистрирован</AuthErrorBanner> : null}

        <div className={styles.inputs}>
          <AuthInput
            {...register('email')}
            id="register-email"
            label="Почта"
            type="email"
            placeholder="Введите почту"
            autoComplete="email"
            className={errorToneClassName}
            errorMessage={errors.email?.message}
          />
          <AuthInput
            {...register('name')}
            id="register-name"
            label="Имя"
            type="text"
            placeholder="Введите имя"
            autoComplete="name"
            className={errorToneClassName}
            errorMessage={errors.name?.message}
          />
          <AuthInput
            {...register('password')}
            id="register-password"
            label="Пароль"
            type="password"
            placeholder="Введите пароль"
            autoComplete="new-password"
            className={errorToneClassName}
            errorMessage={errors.password?.message}
          />
          <AuthInput
            {...register('confirmPassword')}
            id="register-confirm-password"
            label="Повторите пароль"
            type="password"
            placeholder="Повторите пароль"
            autoComplete="new-password"
            className={errorToneClassName}
            errorMessage={errors.confirmPassword?.message}
          />
        </div>

        <div className={styles.buttons}>
          <AuthButtonPrimary disabled={isBusy} type="submit">
            {isBusy ? 'Регистрация...' : 'Зарегистрироваться'}
          </AuthButtonPrimary>
        </div>
      </fieldset>

      {submitError ? <AuthInlineError>{submitError}</AuthInlineError> : null}
    </form>
  )
}

