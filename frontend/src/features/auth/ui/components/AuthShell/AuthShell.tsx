import type { PropsWithChildren } from 'react'
import background from '../../../../../assets/auth-background.svg'
import { BrandHeader } from '../BrandHeader/BrandHeader'
import styles from './AuthShell.module.css'

export function AuthShell({ children }: PropsWithChildren) {
  return (
    <main className={styles.viewport}>
      <section className={styles.canvas} aria-label="PlaylistPass auth">
        <img className={styles.background} src={background} alt="" />
        <div className={styles.overlay}>
          <BrandHeader />
          {children}
        </div>
      </section>
    </main>
  )
}
