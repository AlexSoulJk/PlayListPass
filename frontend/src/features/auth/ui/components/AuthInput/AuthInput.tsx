import { forwardRef, useState, type InputHTMLAttributes } from 'react'
import styles from './AuthInput.module.css'

type AuthInputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string
  errorMessage?: string
}

export const AuthInput = forwardRef<HTMLInputElement, AuthInputProps>(function AuthInput(
  { id, label, errorMessage, className, type = 'text', ...inputProps },
  ref,
) {
  const [isPasswordVisible, setIsPasswordVisible] = useState(false)
  const controlId = id ?? label.toLowerCase().replace(/\s+/g, '-')
  const errorId = `${controlId}-error`
  const isPasswordField = type === 'password'
  const resolvedType = isPasswordField && isPasswordVisible ? 'text' : type

  const rootClassName = [styles.input, className, Boolean(errorMessage) ? styles.inputError : '', isPasswordField ? styles.inputWithToggle : '']
    .filter(Boolean)
    .join(' ')

  return (
    <div className={styles.field}>
      <label className="sr-only" htmlFor={controlId}>
        {label}
      </label>
      <div className={styles.control}>
        <input
          {...inputProps}
          className={rootClassName}
          id={controlId}
          type={resolvedType}
          ref={ref}
          aria-invalid={Boolean(errorMessage)}
          aria-describedby={errorMessage ? errorId : undefined}
        />
        {isPasswordField ? (
          <button
            aria-label={isPasswordVisible ? 'Скрыть пароль' : 'Показать пароль'}
            aria-pressed={isPasswordVisible}
            className={styles.passwordToggle}
            onClick={() => setIsPasswordVisible((current) => !current)}
            type="button"
          >
            <svg className={styles.passwordToggleIcon} viewBox="0 0 24 24" aria-hidden>
              <path d="M2 12C3.9 8.9 7.5 6 12 6C16.5 6 20.1 8.9 22 12C20.1 15.1 16.5 18 12 18C7.5 18 3.9 15.1 2 12Z" />
              <circle cx="12" cy="12" r="3.2" />
              {isPasswordVisible ? null : <path d="M4 20L20 4" />}
            </svg>
          </button>
        ) : null}
      </div>
      {errorMessage ? (
        <p className={styles.errorText} id={errorId} role="alert">
          {errorMessage}
        </p>
      ) : null}
    </div>
  )
})
