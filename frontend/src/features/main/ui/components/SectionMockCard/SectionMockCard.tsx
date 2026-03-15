import type { PropsWithChildren } from 'react'
import styles from './SectionMockCard.module.css'

type SectionMockCardProps = PropsWithChildren<{
  title: string
  description: string
}>

export function SectionMockCard({ title, description, children }: SectionMockCardProps) {
  return (
    <section className={styles.card}>
      <h2 className={styles.title}>{title}</h2>
      <p className={styles.description}>{description}</p>
      <div className={styles.content}>{children}</div>
    </section>
  )
}
