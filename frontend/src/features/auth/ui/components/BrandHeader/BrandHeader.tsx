import styles from './BrandHeader.module.css'

export function BrandHeader() {
  return (
    <div className={styles.header}>
      <h1 className={styles.title}>PlaylistPass</h1>
      <p className={styles.subtitle}>Создавайте совместные плейлисты</p>
    </div>
  )
}
