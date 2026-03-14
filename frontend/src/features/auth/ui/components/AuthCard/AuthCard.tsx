import type { PropsWithChildren } from 'react'
import styles from './AuthCard.module.css'

export function AuthCard({ children }: PropsWithChildren) {
  return <section className={styles.card}>{children}</section>
}
