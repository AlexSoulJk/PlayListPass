import type { ButtonHTMLAttributes, PropsWithChildren } from 'react'
import styles from './AuthButtonPrimary.module.css'

type AuthButtonPrimaryProps = ButtonHTMLAttributes<HTMLButtonElement> & PropsWithChildren

export function AuthButtonPrimary({ children, className, ...props }: AuthButtonPrimaryProps) {
  const mergedClassName = className ? `${styles.button} ${className}` : styles.button

  return (
    <button {...props} className={mergedClassName}>
      {children}
    </button>
  )
}
