import { useNavigate } from 'react-router-dom'
import styles from './ConnectServicesPage.module.css'

const services = [
  { id: 'yandex', label: 'Яндекс Музыка', icon: 'Y' },
  { id: 'spotify', label: 'Spotify', icon: 'S' },
  { id: 'youtube', label: 'YouTube', icon: 'YT' },
]

export function ConnectServicesPage() {
  const navigate = useNavigate()

  return (
    <section className={styles.root}>
      <h2 className={styles.title}>Хотите подключить музыкальные сервисы сейчас?</h2>
      <p className={styles.subtitle}>Пока используется моковый набор иконок до загрузки финальных изображений.</p>

      <div className={styles.services}>
        {services.map((service) => (
          <button className={styles.serviceButton} key={service.id} type="button">
            <span className={styles.serviceIcon} aria-hidden>
              {service.icon}
            </span>
            <span>{service.label}</span>
          </button>
        ))}
      </div>

      <section aria-label="Шаг пользовательских кредов" className={styles.credentialsMock}>
        <h3 className={styles.credentialsTitle}>Пользовательские креды сервиса (mock)</h3>
        <p className={styles.credentialsText}>
          Здесь будет форма для ввода токена/логина выбранного сервиса и превью подключенного профиля.
        </p>
      </section>

      <button className={styles.skipButton} onClick={() => navigate('/app/groups')} type="button">
        Пропустить
      </button>
    </section>
  )
}

