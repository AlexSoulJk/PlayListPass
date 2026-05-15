import type { PropsWithChildren } from 'react'
import background from '../../../../../assets/auth-background.svg'
import { BrandHeader } from '../BrandHeader/BrandHeader'
import { ServicesFooterLogos } from '../ServicesFooterLogos/ServicesFooterLogos'
import styles from './AuthShell.module.css'

export function AuthShell({ children }: PropsWithChildren) {
  return (
    <main className={styles.viewport}>
      <section className={styles.canvas} aria-label="PlaylistPass auth">
        <img className={styles.background} src={background} alt="" />
        <div className={styles.overlay}>
          <div className={styles.content}>
            <BrandHeader />
            {children}
          </div>
          <ServicesFooterLogos />
        </div>
      </section>
    </main>
  )
}
