import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { useAuth } from '../../../../../app/providers/useAuth'
import { AuthApiError } from '../../../api/authApi'
import type { AuthErrorCode } from '../../../types'
import { AuthButtonPrimary } from '../../components/AuthButtonPrimary/AuthButtonPrimary'
import { AuthButtonSecondary } from '../../components/AuthButtonSecondary/AuthButtonSecondary'
import { AuthInlineError } from '../../components/AuthInlineError/AuthInlineError'
import { AuthInput } from '../../components/AuthInput/AuthInput'
import styles from './LoginForm.module.css'

const loginSchema = z.object({
  email: z.string().email('Введите корректную почту'),
  password: z.string().min(8, 'Минимум 8 символов'),
})

type LoginFormValues = z.infer<typeof loginSchema>

export function LoginForm() {
  const navigate = useNavigate()
  const { signIn } = useAuth()
  const [authError, setAuthError] = useState<AuthErrorCode | null>(null)

  const {
    register,
    handleSubmit,
    setFocus,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  })

  const onSubmit = handleSubmit(async (values) => {
    setAuthError(null)

    try {
      await signIn(values)
      navigate('/app', { replace: true })
    } catch (error) {
      if (error instanceof AuthApiError) {
        setAuthError(error.code)

        if (error.code === 'INVALID_CREDENTIALS') {
          setValue('password', '')
          setFocus('password')
        }

        return
      }

      setAuthError('UNKNOWN')
    }
  })

  const submitDisabled = isSubmitting
  const invalidCredentials = authError === 'INVALID_CREDENTIALS'

  const emailError = errors.email?.message
  const passwordError = errors.password?.message ?? (invalidCredentials ? 'Неверные почта или пароль' : undefined)

  return (
    <form className={styles.form} onSubmit={onSubmit} noValidate>
      <div className={styles.inputs}>
        <AuthInput
          {...register('email')}
          id="login-email"
          label="Почта"
          type="email"
          placeholder="Введите почту или номер телефона"
          autoComplete="email"
          errorMessage={emailError}
        />
        <AuthInput
          {...register('password')}
          id="login-password"
          label="Пароль"
          type="password"
          placeholder="Введите пароль"
          autoComplete="current-password"
          errorMessage={passwordError}
        />
      </div>

      <div className={styles.buttons}>
        <AuthButtonPrimary disabled={submitDisabled} type="submit">
          {submitDisabled ? 'Вход...' : 'Войти'}
        </AuthButtonPrimary>
        <AuthButtonSecondary onClick={() => navigate('/')} type="button">
          Назад
        </AuthButtonSecondary>
      </div>

      {authError === 'NETWORK_ERROR' ? (
        <AuthInlineError>Проблема с сетью. Проверьте подключение и попробуйте снова.</AuthInlineError>
      ) : null}
      {authError === 'UNKNOWN' ? <AuthInlineError>Не удалось выполнить вход. Повторите попытку.</AuthInlineError> : null}
    </form>
  )
}
