import type { PropsWithChildren } from 'react'
import styles from './AuthCard.module.css'

type AuthCardProps = PropsWithChildren<{
  className?: string
}>

export function AuthCard({ children, className }: AuthCardProps) {
  const cardClassName = className ? `${styles.card} ${className}` : styles.card

  return <section className={cardClassName}>{children}</section>
}
