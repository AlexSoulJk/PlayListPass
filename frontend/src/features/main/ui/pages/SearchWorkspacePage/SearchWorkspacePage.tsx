import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../../../../app/providers/useAuth'
import { getGroupList, getGroupPlaylists, getGroupUsers, GroupsApiError } from '../../../../groups/api/groupsApi'
import type { GroupListItem, GroupPlaylistItem, GroupRole } from '../../../../groups/models/types'
import { addTrackToPlaylist, searchTracks, SearchApiError } from '../../../api/searchApi'
import type {
  AddTrackToPlaylistPayload,
  SearchRouteState,
  SearchTrackItem,
  StreamingService,
} from '../../../models/searchTypes'
import styles from './SearchWorkspacePage.module.css'

type ServiceFilterItem = {
  id: StreamingService
  label: string
}

type ToastState = {
  text: string
  tone: 'success' | 'error'
}

const serviceFilters: ServiceFilterItem[] = [
  { id: 'YANDEX_MUSIC', label: 'Yandex Music' },
  { id: 'YOUTUBE', label: 'YouTube' },
  { id: 'SPOTIFY', label: 'Spotify' },
]

const defaultAvailability: Record<StreamingService, boolean> = {
  YANDEX_MUSIC: true,
  YOUTUBE: false,
  SPOTIFY: false,
}

const serviceVisualMap: Record<StreamingService, { short: string; full: string; urlPrefix: string }> = {
  YANDEX_MUSIC: { short: 'Y', full: 'Яндекс Музыка', urlPrefix: 'https://music.yandex.ru/track/' },
  YOUTUBE: { short: 'YT', full: 'YouTube Music', urlPrefix: 'https://music.youtube.com/watch?v=' },
  SPOTIFY: { short: 'S', full: 'Spotify', urlPrefix: 'https://open.spotify.com/track/' },
}

const roleToLabel: Record<GroupRole, string> = {
  MAINTAINER: 'host',
  GUEST: 'guest',
  VIEWER: 'viewer',
}

const normalizeEmail = (email: string | null | undefined): string => {
  return (email ?? '').trim().toLowerCase()
}

const toUiErrorText = (error: unknown): string => {
  if (error instanceof SearchApiError) {
    switch (error.code) {
      case 'UNAUTHORIZED':
        return 'Сессия истекла. Авторизуйтесь повторно.'
      case 'GROUP_NOT_FOUND':
        return 'Группа не найдена.'
      case 'PLAYLIST_NOT_FOUND':
        return 'Плейлист не найден.'
      case 'TRACK_NOT_FOUND':
        return 'Трек не найден.'
      case 'GROUP_TRACK_EDIT_FORBIDDEN':
        return 'Недостаточно прав для добавления треков.'
      case 'PLAYLIST_TRACK_ALREADY_EXISTS':
        return 'Уже в плейлисте.'
      case 'TRACK_SOURCE_REQUIRED':
        return 'Не указан источник трека.'
      case 'TRACK_METADATA_REQUIRED':
        return 'Не хватает данных трека для добавления.'
      case 'TRACK_EXTERNAL_URL_REQUIRED':
        return 'Для нового трека нужен внешний URL.'
      case 'VALIDATION_ERROR':
        return 'Проверьте корректность данных.'
      case 'NETWORK_ERROR':
        return 'Сеть недоступна или backend не отвечает.'
      default:
        return error.message
    }
  }

  if (error instanceof GroupsApiError) {
    switch (error.code) {
      case 'UNAUTHORIZED':
        return 'Сессия истекла. Авторизуйтесь повторно.'
      case 'GROUP_NOT_FOUND':
        return 'Группа не найдена.'
      case 'ACCESS_DENIED':
      case 'MAINTAINER_REQUIRED':
        return 'Нет доступа к группе.'
      case 'NETWORK_ERROR':
        return 'Сеть недоступна или backend не отвечает.'
      default:
        return error.message
    }
  }

  return 'Произошла непредвиденная ошибка. Повторите попытку.'
}

export function SearchWorkspacePage() {
  const { session } = useAuth()
  const location = useLocation()
  const routeState = (location.state as SearchRouteState | null) ?? null

  const accessToken = session?.accessToken ?? null
  const sessionEmail = normalizeEmail(session?.email)

  const [groups, setGroups] = useState<GroupListItem[]>([])
  const [playlists, setPlaylists] = useState<GroupPlaylistItem[]>(routeState?.playlists ?? [])
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(routeState?.groupId ?? null)
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<string | null>(routeState?.playlistId ?? null)
  const [actualRole, setActualRole] = useState<GroupRole | null>(routeState?.groupRole ?? null)

  const [query, setQuery] = useState('')
  const [selectedServices, setSelectedServices] = useState<StreamingService[]>(['YANDEX_MUSIC'])
  const [serviceAvailability, setServiceAvailability] = useState<Record<StreamingService, boolean>>(defaultAvailability)

  const [items, setItems] = useState<SearchTrackItem[]>([])
  const [page, setPage] = useState(1)
  const [pageSize] = useState(8)
  const [totalPages, setTotalPages] = useState(1)
  const [totalItems, setTotalItems] = useState(0)

  const [openMenuTrackKey, setOpenMenuTrackKey] = useState<string | null>(null)
  const [trackInfoModal, setTrackInfoModal] = useState<SearchTrackItem | null>(null)
  const [addPlaylistPickerTrackKey, setAddPlaylistPickerTrackKey] = useState<string | null>(null)

  const [errorText, setErrorText] = useState<string | null>(null)
  const [toast, setToast] = useState<ToastState | null>(null)

  const [isGroupsLoading, setIsGroupsLoading] = useState(false)
  const [isGroupDataLoading, setIsGroupDataLoading] = useState(false)
  const [isSearchLoading, setIsSearchLoading] = useState(false)
  const [isAddLoading, setIsAddLoading] = useState(false)
  const [isGroupDropdownOpen, setIsGroupDropdownOpen] = useState(false)
  const [isPlaylistDropdownOpen, setIsPlaylistDropdownOpen] = useState(false)

  const selectedGroup = useMemo(
    () => groups.find((group) => group.id === selectedGroupId) ?? null,
    [groups, selectedGroupId],
  )
  const selectedPlaylist = useMemo(
    () => playlists.find((playlist) => playlist.id === selectedPlaylistId) ?? null,
    [playlists, selectedPlaylistId],
  )

  const canAddTrack = actualRole === 'MAINTAINER' || actualRole === 'GUEST'
  const roleLabel = actualRole ? roleToLabel[actualRole] : 'роль не определена'
  const selectedGroupLabel = selectedGroup?.name ?? 'Группа'
  const heroGroupTitle = selectedGroup?.name ?? routeState?.groupName ?? 'Группа не выбрана'
  const selectedPlaylistLabel = selectedPlaylist?.name ?? 'Плейлист не выбран'
  const heroImageUrl = selectedGroup?.image_url ?? routeState?.groupImageUrl ?? null
  const heroStyle = heroImageUrl
    ? {
        backgroundImage: `linear-gradient(90deg, rgba(0,0,0,0.45), rgba(0,0,0,0.3)), url(${heroImageUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }
    : undefined
  const heroAvatarStyle = heroImageUrl
    ? {
        backgroundImage: `url(${heroImageUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }
    : undefined

  useEffect(() => {
    if (!accessToken) {
      setGroups([])
      setPlaylists([])
      setSelectedGroupId(null)
      setSelectedPlaylistId(null)
      setActualRole(null)
      return
    }

    let isMounted = true
    const loadGroups = async () => {
      setIsGroupsLoading(true)
      setErrorText(null)
      try {
        const loadedGroups = await getGroupList(accessToken)
        if (!isMounted) {
          return
        }
        setGroups(loadedGroups)
        if (routeState?.groupId && loadedGroups.some((group) => group.id === routeState.groupId)) {
          setSelectedGroupId(routeState.groupId)
          return
        }
        setSelectedGroupId((previousGroupId) => {
          if (previousGroupId && loadedGroups.some((group) => group.id === previousGroupId)) {
            return previousGroupId
          }
          return loadedGroups[0]?.id ?? null
        })
      } catch (error) {
        if (!isMounted) {
          return
        }
        setErrorText(toUiErrorText(error))
      } finally {
        if (isMounted) {
          setIsGroupsLoading(false)
        }
      }
    }

    void loadGroups()
    return () => {
      isMounted = false
    }
  }, [accessToken, routeState?.groupId])

  useEffect(() => {
    if (!accessToken || !selectedGroupId) {
      setPlaylists([])
      setSelectedPlaylistId(null)
      setActualRole(null)
      return
    }

    let isMounted = true
    const loadGroupData = async () => {
      setIsGroupDataLoading(true)
      setErrorText(null)
      try {
        const [groupPlaylists, groupUsers] = await Promise.all([
          getGroupPlaylists(accessToken, selectedGroupId),
          getGroupUsers(accessToken, selectedGroupId),
        ])
        if (!isMounted) {
          return
        }

        setPlaylists(groupPlaylists)

        const currentUser = groupUsers.find((member) => normalizeEmail(member.email) === sessionEmail) ?? null
        setActualRole(currentUser?.role ?? null)

        setSelectedPlaylistId((previousPlaylistId) => {
          if (routeState?.playlistId && routeState.groupId === selectedGroupId) {
            const fromRoute = groupPlaylists.find((playlist) => playlist.id === routeState.playlistId)
            if (fromRoute) {
              return fromRoute.id
            }
          }
          if (previousPlaylistId && groupPlaylists.some((playlist) => playlist.id === previousPlaylistId)) {
            return previousPlaylistId
          }
          return null
        })
      } catch (error) {
        if (!isMounted) {
          return
        }
        setPlaylists([])
        setSelectedPlaylistId(null)
        setActualRole(null)
        setErrorText(toUiErrorText(error))
      } finally {
        if (isMounted) {
          setIsGroupDataLoading(false)
        }
      }
    }

    void loadGroupData()
    return () => {
      isMounted = false
    }
  }, [accessToken, selectedGroupId, sessionEmail, routeState?.playlistId, routeState?.groupId])

  useEffect(() => {
    if (!toast) {
      return
    }
    const timeoutId = window.setTimeout(() => setToast(null), 2200)
    return () => window.clearTimeout(timeoutId)
  }, [toast])

  const runSearch = async (targetPage: number) => {
    if (!accessToken || !selectedGroupId) {
      setErrorText('Выберите группу для поиска.')
      return
    }

    const trimmedQuery = query.trim()
    if (!trimmedQuery) {
      setErrorText('Введите запрос для поиска.')
      return
    }

    const enabledServices = selectedServices.filter((service) => serviceAvailability[service])
    if (enabledServices.length === 0) {
      setErrorText('Нет доступных сервисов для поиска.')
      return
    }

    setErrorText(null)
    setIsSearchLoading(true)
    setOpenMenuTrackKey(null)
    setAddPlaylistPickerTrackKey(null)
    try {
      const response = await searchTracks(accessToken, {
        group_id: selectedGroupId,
        query: trimmedQuery,
        services: enabledServices,
        page: targetPage,
        page_size: pageSize,
      })
      setItems(response.items)
      setPage(response.pagination.page)
      setTotalPages(response.pagination.pages)
      setTotalItems(response.pagination.total)
      setServiceAvailability((previous) => ({
        ...previous,
        ...response.service_availability,
      }))
    } catch (error) {
      setItems([])
      setPage(1)
      setTotalPages(1)
      setTotalItems(0)
      setErrorText(toUiErrorText(error))
    } finally {
      setIsSearchLoading(false)
    }
  }

  const handleSubmitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    void runSearch(1)
  }

  const toggleServiceFilter = (service: StreamingService) => {
    if (!serviceAvailability[service]) {
      return
    }
    setSelectedServices((previous) => {
      if (previous.includes(service)) {
        if (previous.length === 1) {
          return previous
        }
        return previous.filter((item) => item !== service)
      }
      return [...previous, service]
    })
  }

  const toTrackKey = (item: SearchTrackItem): string => {
    return `${item.service}:${item.service_track_id}:${item.internal_track_id ?? 'external'}`
  }

  const buildAddPayload = (track: SearchTrackItem): AddTrackToPlaylistPayload => {
    if (track.internal_track_id) {
      return { internal_track_id: track.internal_track_id }
    }
    return {
      service: track.service,
      service_track_id: track.service_track_id,
      title: track.title,
      artist: track.artist,
      cover_url: track.cover_url,
      external_url: track.external_url,
      duration_sec: track.duration_sec,
      imported_from_search: true,
    }
  }

  const pushToast = (text: string, tone: ToastState['tone']) => {
    setToast({ text, tone })
  }

  const addTrack = async (track: SearchTrackItem, playlistId: string) => {
    if (!accessToken || !selectedGroupId) {
      setErrorText('Не удалось определить группу для добавления трека.')
      return
    }

    setIsAddLoading(true)
    setErrorText(null)
    try {
      await addTrackToPlaylist(
        accessToken,
        selectedGroupId,
        playlistId,
        buildAddPayload(track),
      )
      pushToast('Трек добавлен в плейлист', 'success')
      setOpenMenuTrackKey(null)
      setAddPlaylistPickerTrackKey(null)
    } catch (error) {
      const message = toUiErrorText(error)
      setErrorText(message)
      pushToast(message, 'error')
    } finally {
      setIsAddLoading(false)
    }
  }

  const handleAddTrackClick = (track: SearchTrackItem, trackKey: string) => {
    if (!canAddTrack) {
      return
    }
    if (selectedPlaylistId) {
      void addTrack(track, selectedPlaylistId)
      return
    }
    setAddPlaylistPickerTrackKey((previous) => (previous === trackKey ? null : trackKey))
  }

  const resolveTrackServiceMeta = (service: StreamingService): { short: string; full: string } => {
    return serviceVisualMap[service] ?? { short: '•', full: service }
  }

  const resolveTrackServiceUrl = (track: SearchTrackItem): string | null => {
    if (track.external_url) {
      return track.external_url
    }
    const mapping = serviceVisualMap[track.service]
    if (!mapping) {
      return null
    }
    return `${mapping.urlPrefix}${track.service_track_id}`
  }

  return (
    <section className={styles.root}>
      <header className={styles.hero} style={heroStyle}>
        <div className={styles.heroTop}>
          <div className={styles.heroGroup}>
            <span aria-hidden className={styles.heroGroupAvatar} style={heroAvatarStyle} />
            <h2 className={styles.heroTitle}>{heroGroupTitle}</h2>
          </div>
          <span className={styles.heroRole}>{roleLabel}</span>
        </div>
        <p className={styles.heroSubtitle}>Добавление треков в плейлисты</p>
      </header>

      <section className={styles.filtersCard}>
        <div className={styles.filterBar}>
          <div className={styles.dropdownWrap}>
            <button
              aria-expanded={isGroupDropdownOpen}
              className={styles.dropdownTrigger}
              onClick={() => {
                setIsGroupDropdownOpen((previous) => !previous)
                setIsPlaylistDropdownOpen(false)
              }}
              type="button"
            >
              {selectedGroupLabel}
              <span className={styles.chevron}>▼</span>
            </button>
            {isGroupDropdownOpen ? (
              <div className={styles.dropdownMenu}>
                {groups.map((group) => (
                  <button
                    className={
                      selectedGroupId === group.id
                        ? `${styles.dropdownItem} ${styles.dropdownItemActive}`
                        : styles.dropdownItem
                    }
                    key={group.id}
                    onClick={() => {
                      setSelectedGroupId(group.id)
                      setSelectedPlaylistId(null)
                      setItems([])
                      setTotalItems(0)
                      setPage(1)
                      setTotalPages(1)
                      setIsGroupDropdownOpen(false)
                    }}
                    type="button"
                  >
                    {group.name}
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          <div className={styles.dropdownWrap}>
            <button
              aria-expanded={isPlaylistDropdownOpen}
              className={styles.dropdownTrigger}
              onClick={() => {
                setIsPlaylistDropdownOpen((previous) => !previous)
                setIsGroupDropdownOpen(false)
              }}
              type="button"
            >
              {selectedPlaylistLabel}
              <span className={styles.chevron}>▼</span>
            </button>
            {isPlaylistDropdownOpen ? (
              <div className={styles.dropdownMenu}>
                <button
                  className={
                    selectedPlaylistId === null
                      ? `${styles.dropdownItem} ${styles.dropdownItemActive}`
                      : styles.dropdownItem
                  }
                  onClick={() => {
                    setSelectedPlaylistId(null)
                    setIsPlaylistDropdownOpen(false)
                  }}
                  type="button"
                >
                  Не выбран
                </button>
                {playlists.map((playlist) => (
                  <button
                    className={
                      selectedPlaylistId === playlist.id
                        ? `${styles.dropdownItem} ${styles.dropdownItemActive}`
                        : styles.dropdownItem
                    }
                    key={playlist.id}
                    onClick={() => {
                      setSelectedPlaylistId(playlist.id)
                      setIsPlaylistDropdownOpen(false)
                    }}
                    type="button"
                  >
                    {playlist.name}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>

        <p className={styles.playlistHint}>Текущий плейлист: {selectedPlaylistLabel}</p>

        <div className={styles.serviceFilters}>
          {serviceFilters.map((service) => {
            const enabled = serviceAvailability[service.id]
            const selected = selectedServices.includes(service.id)
            return (
              <button
                className={
                  selected
                    ? `${styles.servicePill} ${styles.servicePillSelected}`
                    : styles.servicePill
                }
                disabled={!enabled}
                key={service.id}
                onClick={() => toggleServiceFilter(service.id)}
                title={enabled ? service.label : 'Не подключен сервис'}
                type="button"
              >
                {service.label}
              </button>
            )
          })}
        </div>

        <form className={styles.searchForm} onSubmit={handleSubmitSearch}>
          <input
            className={styles.searchInput}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Название трека или исполнитель"
            value={query}
          />
          <button className={styles.searchButton} disabled={isSearchLoading || isGroupDataLoading} type="submit">
            {isSearchLoading ? 'Поиск...' : 'Поиск'}
          </button>
        </form>
      </section>

      {errorText ? <p className={styles.errorText}>{errorText}</p> : null}

      <section className={styles.resultsCard}>
        {isGroupsLoading || isGroupDataLoading ? (
          <p className={styles.emptyState}>Загружаем данные группы...</p>
        ) : null}
        {!isGroupsLoading && !isGroupDataLoading && !isSearchLoading && items.length === 0 ? (
          <p className={styles.emptyState}>По запросу пока ничего не найдено.</p>
        ) : null}
        {isSearchLoading ? <p className={styles.emptyState}>Ищем треки...</p> : null}

        {!isSearchLoading
          ? items.map((item) => {
              const trackKey = toTrackKey(item)
              const isMenuOpen = openMenuTrackKey === trackKey
              const isAddPlaylistPickerOpen = addPlaylistPickerTrackKey === trackKey && !selectedPlaylistId
              const serviceMeta = resolveTrackServiceMeta(item.service)
              return (
                <article className={styles.trackRow} key={trackKey}>
                  <span
                    aria-hidden
                    className={styles.trackCover}
                    style={item.cover_url ? { backgroundImage: `url(${item.cover_url})` } : undefined}
                  />
                  <span className={styles.serviceIcon}>{serviceMeta.short}</span>
                  <div className={styles.trackMeta}>
                    <p className={styles.trackTitle}>{item.title}</p>
                    <p className={styles.trackArtist}>{item.artist}</p>
                  </div>
                  {item.is_in_db ? (
                    <span aria-label="Трек уже в базе" className={styles.dbMark} title="Трек уже в базе">
                      ✓
                    </span>
                  ) : null}
                  {canAddTrack ? (
                    <div className={styles.menuWrap}>
                      <button
                        className={styles.menuButton}
                        onClick={() => {
                          setOpenMenuTrackKey((previous) => (previous === trackKey ? null : trackKey))
                          setAddPlaylistPickerTrackKey(null)
                        }}
                        type="button"
                      >
                        ...
                      </button>
                      {isMenuOpen ? (
                        <>
                          <div className={styles.menuPopup}>
                            <button className={styles.menuItem} onClick={() => handleAddTrackClick(item, trackKey)} type="button">
                              Добавить в плейлист
                            </button>
                            <button
                              className={styles.menuItem}
                              onClick={() => {
                                setTrackInfoModal(item)
                                setOpenMenuTrackKey(null)
                                setAddPlaylistPickerTrackKey(null)
                              }}
                              type="button"
                            >
                              О треке
                            </button>
                          </div>
                          {isAddPlaylistPickerOpen ? (
                            <div className={styles.inlinePlaylistPicker}>
                              {playlists.length === 0 ? (
                                <p className={styles.inlinePlaylistEmpty}>В группе нет плейлистов</p>
                              ) : null}
                              {playlists.map((playlist) => (
                                <button
                                  className={styles.inlinePlaylistItem}
                                  disabled={isAddLoading}
                                  key={playlist.id}
                                  onClick={() => void addTrack(item, playlist.id)}
                                  type="button"
                                >
                                  {playlist.name}
                                </button>
                              ))}
                            </div>
                          ) : null}
                        </>
                      ) : null}
                    </div>
                  ) : (
                    <button
                      className={styles.menuGhostButton}
                      onClick={() => setTrackInfoModal(item)}
                      type="button"
                    >
                      О треке
                    </button>
                  )}
                </article>
              )
            })
          : null}
      </section>

      {totalItems > 0 ? (
        <footer className={styles.pagination}>
          <button
            className={styles.pageButton}
            disabled={page <= 1 || isSearchLoading}
            onClick={() => void runSearch(page - 1)}
            type="button"
          >
            Назад
          </button>
          <span className={styles.pageLabel}>
            {page} / {totalPages}
          </span>
          <button
            className={styles.pageButton}
            disabled={page >= totalPages || isSearchLoading}
            onClick={() => void runSearch(page + 1)}
            type="button"
          >
            Вперед
          </button>
        </footer>
      ) : null}

      {trackInfoModal ? (
        <div aria-modal className={styles.modalOverlay} onClick={() => setTrackInfoModal(null)} role="dialog">
          <div className={styles.modalCard} onClick={(event) => event.stopPropagation()}>
            <span
              aria-hidden
              className={styles.modalCover}
              style={trackInfoModal.cover_url ? { backgroundImage: `url(${trackInfoModal.cover_url})` } : undefined}
            />
            <h3 className={styles.modalTitle}>О треке</h3>
            <div className={styles.modalGrid}>
              <p><strong>Название:</strong> {trackInfoModal.title}</p>
              <p><strong>Исполнитель:</strong> {trackInfoModal.artist}</p>
              <p><strong>Сервис:</strong> {resolveTrackServiceMeta(trackInfoModal.service).full}</p>
              {resolveTrackServiceUrl(trackInfoModal) ? (
                <p>
                  <strong>Ссылка:</strong>{' '}
                  <a
                    className={styles.trackLink}
                    href={resolveTrackServiceUrl(trackInfoModal) ?? undefined}
                    rel="noreferrer"
                    target="_blank"
                  >
                    Открыть в сервисе
                  </a>
                </p>
              ) : null}
            </div>
            <button className={styles.closeButton} onClick={() => setTrackInfoModal(null)} type="button">
              Закрыть
            </button>
          </div>
        </div>
      ) : null}

      {toast ? (
        <div className={toast.tone === 'success' ? styles.toastSuccess : styles.toastError}>
          {toast.text}
        </div>
      ) : null}
    </section>
  )
}
