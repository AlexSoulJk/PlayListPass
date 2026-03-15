import { SectionMockCard } from '../../components/SectionMockCard/SectionMockCard'
import styles from './ProfileWorkspacePage.module.css'

export function ProfileWorkspacePage() {
  return (
    <SectionMockCard
      description="Мок личного кабинета. Здесь появятся настройки профиля, подключенные сервисы и управление данными."
      title="Личный кабинет"
    >
      <div className={styles.grid}>
        <div className={styles.block}>Профиль пользователя</div>
        <div className={styles.block}>Подключенные сервисы</div>
        <div className={styles.block}>Безопасность аккаунта</div>
        <div className={styles.block}>Настройки уведомлений</div>
      </div>
    </SectionMockCard>
  )
}
