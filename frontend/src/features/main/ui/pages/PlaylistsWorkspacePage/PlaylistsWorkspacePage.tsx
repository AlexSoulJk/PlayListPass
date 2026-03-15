import { SectionMockCard } from '../../components/SectionMockCard/SectionMockCard'
import styles from './PlaylistsWorkspacePage.module.css'

const mockPlaylists = ['Общий плейлист #1', 'Вечерний сет #2', 'Выходные #3']

export function PlaylistsWorkspacePage() {
  return (
    <SectionMockCard
      description="Мок раздела плейлистов. Здесь будет управление списками треков и привязка к группам."
      title="Плейлисты"
    >
      <div className={styles.toolbar}>Панель действий (mock)</div>
      <div className={styles.list}>
        {mockPlaylists.map((playlist) => (
          <article className={styles.item} key={playlist}>
            <h3 className={styles.itemTitle}>{playlist}</h3>
            <p className={styles.itemMeta}>12 треков • обновлено 2 часа назад</p>
          </article>
        ))}
      </div>
    </SectionMockCard>
  )
}
