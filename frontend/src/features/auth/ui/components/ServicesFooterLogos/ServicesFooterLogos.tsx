import styles from './ServicesFooterLogos.module.css'

const servicePills = [
  { key: 'yandex', label: 'Яндекс Музыка', icon: 'Y', href: 'https://music.yandex.ru/' },
  { key: 'spotify', label: 'Spotify', icon: 'S', href: 'https://open.spotify.com/' },
  { key: 'youtube', label: 'YouTube', icon: 'YT', href: 'https://music.youtube.com/' },
]

type ServicesFooterLogosProps = {
  className?: string
}

export function ServicesFooterLogos({ className }: ServicesFooterLogosProps) {
  const rootClassName = className ? `${styles.root} ${className}` : styles.root

  return (
    <section aria-label="Музыкальные сервисы" className={rootClassName}>
      {servicePills.map((service) => (
        <a className={styles.pill} href={service.href} key={service.key} rel="noreferrer" target="_blank">
          <span className={styles.icon} aria-hidden>
            {service.icon}
          </span>
          <span className={styles.label}>{service.label}</span>
        </a>
      ))}
    </section>
  )
}
