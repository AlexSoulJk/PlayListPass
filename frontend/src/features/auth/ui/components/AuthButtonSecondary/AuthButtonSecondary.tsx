import type { ButtonHTMLAttributes, PropsWithChildren } from 'react'
import styles from './AuthButtonSecondary.module.css'

type AuthButtonSecondaryProps = ButtonHTMLAttributes<HTMLButtonElement> & PropsWithChildren

export function AuthButtonSecondary({ children, className, ...props }: AuthButtonSecondaryProps) {
  const mergedClassName = className ? `${styles.button} ${className}` : styles.button

  return (
    <button {...props} className={mergedClassName}>
      {children}
    </button>
  )
}
