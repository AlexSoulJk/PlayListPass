import { useLocation } from 'react-router-dom'
import type { GroupPlaylistItem } from '../../../../groups/models/types'
import { SectionMockCard } from '../../components/SectionMockCard/SectionMockCard'
import styles from './PlaylistsWorkspacePage.module.css'

type PlaylistsRouteState = {
  groupId?: string
  groupName?: string
  playlists?: GroupPlaylistItem[]
}

const mockPlaylists = ['Общий плейлист #1', 'Вечерний сет #2', 'Выходные #3']

export function PlaylistsWorkspacePage() {
  const location = useLocation()
  const routeState = (location.state as PlaylistsRouteState | null) ?? null

  const hasGroupPayload = Boolean(routeState?.groupName) && Array.isArray(routeState?.playlists)
  const groupName = routeState?.groupName ?? 'Текущая группа'
  const groupPlaylists = hasGroupPayload ? routeState?.playlists ?? [] : []

  return (
    <SectionMockCard
      description={
        hasGroupPayload
          ? 'Список плейлистов выбранной группы, полученный из раздела групп.'
          : 'Мок раздела плейлистов. Здесь будет управление списками треков и привязка к группам.'
      }
      title="Плейлисты"
    >
      <div className={styles.toolbar}>
        {hasGroupPayload ? `Группа: ${groupName} • Плейлистов: ${groupPlaylists.length}` : 'Панель действий (mock)'}
      </div>

      {hasGroupPayload ? (
        <div className={styles.list}>
          {groupPlaylists.length === 0 ? (
            <article className={styles.item}>
              <h3 className={styles.itemTitle}>Плейлистов пока нет</h3>
              <p className={styles.itemMeta}>Создайте первый плейлист для группы.</p>
            </article>
          ) : (
            groupPlaylists.map((playlist) => (
              <article className={styles.item} key={playlist.id}>
                <h3 className={styles.itemTitle}>{playlist.name}</h3>
                <p className={styles.itemMeta}>Треков в плейлисте: {playlist.track_count}</p>
              </article>
            ))
          )}
        </div>
      ) : (
        <div className={styles.list}>
          {mockPlaylists.map((playlist) => (
            <article className={styles.item} key={playlist}>
              <h3 className={styles.itemTitle}>{playlist}</h3>
              <p className={styles.itemMeta}>12 треков • обновлено 2 часа назад</p>
            </article>
          ))}
        </div>
      )}
    </SectionMockCard>
  )
}
