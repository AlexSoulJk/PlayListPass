import type { PropsWithChildren } from 'react'
import styles from './AuthErrorBanner.module.css'

export function AuthErrorBanner({ children }: PropsWithChildren) {
  return (
    <p className={styles.banner} role="alert">
      {children}
    </p>
  )
}

