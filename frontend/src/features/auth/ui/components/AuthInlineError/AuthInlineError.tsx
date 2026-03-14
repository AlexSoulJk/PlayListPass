import type { PropsWithChildren } from 'react'
import styles from './AuthInlineError.module.css'

export function AuthInlineError({ children }: PropsWithChildren) {
  return (
    <p className={styles.error} role="alert">
      {children}
    </p>
  )
}
