import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../../../../app/providers/useAuth'
import { usePlayback } from '../../../../../app/providers/usePlayback'
import { getGroupList, getGroupPlaylists, getGroupUsers, GroupsApiError } from '../../../../groups/api/groupsApi'
import {
  createPlaylist,
  deletePlaylist,
  getPlaylistPlaybackQueue,
  getPlaylistTracks,
  PlaylistsApiError,
  removeTrackFromPlaylist,
  updatePlaylist,
  uploadPlaylistImage,
} from '../../../../groups/api/playlistsApi'
import type { GroupListItem, GroupPlaylistItem, GroupRole, PlaylistTrackItem } from '../../../../groups/models/types'
import styles from './PlaylistsWorkspacePage.module.css'

type PlaylistsRouteState = {
  groupId?: string
  groupName?: string
  groupImageUrl?: string | null
  groupRole?: GroupRole | null
  playlists?: GroupPlaylistItem[]
}

type RoleFilter = 'ALL' | GroupRole

type ConfirmDialogState = {
  type: 'delete-playlist'
  playlistId: string
  playlistName: string
}

const ALL_GROUPS_FILTER = '__ALL_GROUPS__'
const PLAYBACK_BUFFER_THRESHOLD = 0.25
const PLAYBACK_BUFFER_TIMEOUT_MS = 15000

const roleFilterLabel: Record<RoleFilter, string> = {
  ALL: 'все роли',
  MAINTAINER: 'host',
  GUEST: 'guest',
  VIEWER: 'viewer',
}

const trackServiceVisualMap: Record<PlaylistTrackItem['service'], { short: string; full: string; urlPrefix: string }> = {
  YANDEX_MUSIC: { short: 'Y', full: 'Яндекс Музыка', urlPrefix: 'https://music.yandex.ru/track/' },
  YOUTUBE: { short: 'YT', full: 'YouTube Music', urlPrefix: 'https://music.youtube.com/watch?v=' },
  SPOTIFY: { short: 'S', full: 'Spotify', urlPrefix: 'https://open.spotify.com/track/' },
}

const normalizeEmail = (email: string | null | undefined): string => {
  return (email ?? '').trim().toLowerCase()
}

const toUiErrorText = (error: unknown): string => {
  if (error instanceof PlaylistsApiError) {
    switch (error.code) {
      case 'UNAUTHORIZED':
        return 'Сессия истекла. Авторизуйтесь повторно.'
      case 'GROUP_NOT_FOUND':
        return 'Группа не найдена.'
      case 'PLAYLIST_NOT_FOUND':
        return 'Плейлист не найден.'
      case 'PLAYLIST_TRACK_NOT_FOUND':
        return 'Трек уже удален из плейлиста.'
      case 'PLAYLIST_AUDIO_NOT_AVAILABLE':
        return 'Аудио для треков в этом плейлисте пока недоступно.'
      case 'GROUP_TRACK_EDIT_FORBIDDEN':
        return 'Недостаточно прав для изменения треков.'
      case 'ACCESS_DENIED':
        return 'Недостаточно прав для изменения плейлистов.'
      case 'PLAYLIST_NAME_ALREADY_EXISTS':
        return 'Плейлист с таким названием уже существует в группе.'
      case 'PLAYLIST_IMAGE_UNSUPPORTED_FORMAT':
        return 'Неподдерживаемый формат картинки. Используйте JPG, JPEG, PNG или WEBP.'
      case 'PLAYLIST_IMAGE_OBJECT_NOT_FOUND':
        return 'Картинка не найдена в хранилище. Попробуйте загрузить снова.'
      case 'PLAYLIST_IMAGE_UPLOAD_FAILED':
        return 'Не удалось загрузить файл в хранилище.'
      case 'STORAGE_BACKEND_NOT_AVAILABLE':
        return 'Сервис хранения временно недоступен.'
      case 'VALIDATION_ERROR':
        return 'Проверьте корректность данных формы.'
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
        return 'Нет доступа к данным группы.'
      case 'NETWORK_ERROR':
        return 'Сеть недоступна или backend не отвечает.'
      default:
        return error.message
    }
  }

  return 'Произошла непредвиденная ошибка. Повторите попытку.'
}

const toGroupIdFromFilter = (filterValue: string): string | null => {
  if (!filterValue || filterValue === ALL_GROUPS_FILTER) {
    return null
  }
  return filterValue
}

const toTrackMenuKey = (track: PlaylistTrackItem): string => {
  return `${track.track_id}:${track.service}:${track.service_track_id}`
}

const resolveTrackServiceMeta = (service: PlaylistTrackItem['service']): { short: string; full: string } => {
  return trackServiceVisualMap[service] ?? { short: '•', full: service }
}

const resolveTrackServiceUrl = (track: PlaylistTrackItem): string | null => {
  if (track.external_url) {
    return track.external_url
  }
  const mapping = trackServiceVisualMap[track.service]
  if (!mapping) {
    return null
  }
  return `${mapping.urlPrefix}${track.service_track_id}`
}

const hasBufferedRatio = (audio: HTMLAudioElement, threshold: number): boolean => {
  if (audio.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
    return false
  }
  const duration = audio.duration
  if (!Number.isFinite(duration) || duration <= 0) {
    return audio.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA
  }
  if (audio.buffered.length === 0) {
    return false
  }
  const bufferedEnd = audio.buffered.end(audio.buffered.length - 1)
  return bufferedEnd / duration >= threshold
}

const waitForBufferedPlayback = (
  audio: HTMLAudioElement,
  threshold: number,
  timeoutMs: number,
): Promise<void> => {
  return new Promise((resolve, reject) => {
    let timeoutId: number | undefined
    let isSettled = false

    const cleanup = () => {
      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId)
      }
      audio.removeEventListener('progress', onUpdate)
      audio.removeEventListener('loadedmetadata', onUpdate)
      audio.removeEventListener('canplay', onUpdate)
      audio.removeEventListener('canplaythrough', onUpdate)
      audio.removeEventListener('error', onError)
    }

    const finish = (callback: () => void) => {
      if (isSettled) {
        return
      }
      isSettled = true
      cleanup()
      callback()
    }

    const onUpdate = () => {
      if (hasBufferedRatio(audio, threshold)) {
        finish(resolve)
      }
    }

    const onError = () => {
      finish(() => {
        reject(new Error('AUDIO_BUFFERING_FAILED'))
      })
    }

    audio.addEventListener('progress', onUpdate)
    audio.addEventListener('loadedmetadata', onUpdate)
    audio.addEventListener('canplay', onUpdate)
    audio.addEventListener('canplaythrough', onUpdate)
    audio.addEventListener('error', onError)

    timeoutId = window.setTimeout(() => {
      finish(() => {
        reject(new Error('AUDIO_BUFFERING_TIMEOUT'))
      })
    }, timeoutMs)

    onUpdate()
  })
}

export function PlaylistsWorkspacePage() {
  const location = useLocation()
  const navigate = useNavigate()
  const routeState = (location.state as PlaylistsRouteState | null) ?? null
  const { session } = useAuth()
  const { playTrack } = usePlayback()

  const initialPlaylists = useMemo(() => routeState?.playlists ?? [], [routeState?.playlists])
  const [groups, setGroups] = useState<GroupListItem[]>([])
  const [playlists, setPlaylists] = useState<GroupPlaylistItem[]>(initialPlaylists)

  const [draftGroupFilter, setDraftGroupFilter] = useState<string>(routeState?.groupId ?? '')
  const [appliedGroupFilter, setAppliedGroupFilter] = useState<string>(routeState?.groupId ?? '')
  const [draftRoleFilter, setDraftRoleFilter] = useState<RoleFilter>(routeState?.groupRole ?? 'ALL')
  const [appliedRoleFilter, setAppliedRoleFilter] = useState<RoleFilter>(routeState?.groupRole ?? 'ALL')
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<string | null>(null)
  const [actualRole, setActualRole] = useState<GroupRole | null>(routeState?.groupRole ?? null)

  const [isGroupsLoading, setIsGroupsLoading] = useState(false)
  const [isDataLoading, setIsDataLoading] = useState(false)
  const [isTracksLoading, setIsTracksLoading] = useState(false)
  const [isPlaybackLoading, setIsPlaybackLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isTrackActionLoading, setIsTrackActionLoading] = useState(false)

  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false)
  const [isGroupDropdownOpen, setIsGroupDropdownOpen] = useState(false)
  const [isRoleDropdownOpen, setIsRoleDropdownOpen] = useState(false)

  const [isCreateMode, setIsCreateMode] = useState(false)
  const [createName, setCreateName] = useState('')
  const [createImageFile, setCreateImageFile] = useState<File | null>(null)
  const [createImagePreviewUrl, setCreateImagePreviewUrl] = useState<string | null>(null)

  const [isEditMode, setIsEditMode] = useState(false)
  const [editName, setEditName] = useState('')
  const [editImageFile, setEditImageFile] = useState<File | null>(null)
  const [editImagePreviewUrl, setEditImagePreviewUrl] = useState<string | null>(null)

  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialogState | null>(null)
  const [isConfirmSubmitting, setIsConfirmSubmitting] = useState(false)
  const [errorText, setErrorText] = useState<string | null>(null)
  const [playlistTracks, setPlaylistTracks] = useState<PlaylistTrackItem[]>([])
  const [openTrackMenuKey, setOpenTrackMenuKey] = useState<string | null>(null)
  const [trackInfoModal, setTrackInfoModal] = useState<PlaylistTrackItem | null>(null)

  const accessToken = session?.accessToken ?? null
  const sessionEmail = normalizeEmail(session?.email)

  const appliedGroupId = toGroupIdFromFilter(appliedGroupFilter)
  const appliedGroup = appliedGroupId ? groups.find((group) => group.id === appliedGroupId) ?? null : null
  const selectedPlaylist = playlists.find((playlist) => playlist.id === selectedPlaylistId) ?? null

  const displayRole: RoleFilter = appliedRoleFilter === 'ALL' ? actualRole ?? 'ALL' : appliedRoleFilter
  const canManageGroupPlaylists = Boolean(appliedGroupId) && actualRole === 'MAINTAINER'
  const canManageSelectedPlaylist = canManageGroupPlaylists && Boolean(selectedPlaylist)
  const canEditTracks = Boolean(selectedPlaylist) && (actualRole === 'MAINTAINER' || actualRole === 'GUEST')
  const canPlaySelectedPlaylist = Boolean(selectedPlaylist) && !isPlaybackLoading

  const roleFilterMismatch =
    Boolean(appliedGroupId) &&
    appliedRoleFilter !== 'ALL' &&
    actualRole !== null &&
    actualRole !== appliedRoleFilter

  const hasPendingFilterChanges = draftGroupFilter !== appliedGroupFilter || draftRoleFilter !== appliedRoleFilter
  const canApplyFilters = hasPendingFilterChanges && !isDataLoading && !isSubmitting

  const resolveGroupLabel = (groupFilterValue: string): string => {
    if (groupFilterValue === ALL_GROUPS_FILTER) {
      return 'Все группы'
    }
    if (!groupFilterValue) {
      return 'Группа'
    }
    const selectedGroup = groups.find((group) => group.id === groupFilterValue)
    if (selectedGroup) {
      return selectedGroup.name
    }
    if (routeState?.groupId === groupFilterValue && routeState.groupName) {
      return routeState.groupName
    }
    return 'Группа'
  }

  const appliedGroupLabel = resolveGroupLabel(appliedGroupFilter)
  const draftGroupLabel = resolveGroupLabel(draftGroupFilter)
  const draftRoleLabel = roleFilterLabel[draftRoleFilter === 'ALL' ? actualRole ?? 'ALL' : draftRoleFilter]

  const heroImageUrl =
    appliedGroupId && appliedGroup ? appliedGroup.image_url ?? routeState?.groupImageUrl ?? null : null
  const heroStyle = heroImageUrl
    ? {
        backgroundImage: `linear-gradient(90deg, rgba(0, 0, 0, 0.42), rgba(0, 0, 0, 0.32)), url(${heroImageUrl})`,
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

  const createImageLabel = createImageFile ? `Файл: ${createImageFile.name}` : ''
  const createImagePreviewStyle = createImagePreviewUrl
    ? {
        backgroundImage: `url(${createImagePreviewUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }
    : undefined

  const editImageLabel = editImageFile ? `Файл: ${editImageFile.name}` : ''
  const editImagePreviewStyle = editImagePreviewUrl
    ? {
        backgroundImage: `url(${editImagePreviewUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }
    : selectedPlaylist?.image_url
      ? {
          backgroundImage: `url(${selectedPlaylist.image_url})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }
      : undefined

  const syncGroups = async (token: string) => {
    setIsGroupsLoading(true)
    setErrorText(null)
    try {
      const loadedGroups = await getGroupList(token)
      setGroups(loadedGroups)

      setDraftGroupFilter((previousGroupFilter) => {
        if (previousGroupFilter === ALL_GROUPS_FILTER) {
          return previousGroupFilter
        }
        if (previousGroupFilter && loadedGroups.some((group) => group.id === previousGroupFilter)) {
          return previousGroupFilter
        }
        return loadedGroups[0]?.id ?? ''
      })

      setAppliedGroupFilter((previousGroupFilter) => {
        if (previousGroupFilter === ALL_GROUPS_FILTER) {
          return previousGroupFilter
        }
        if (previousGroupFilter && loadedGroups.some((group) => group.id === previousGroupFilter)) {
          return previousGroupFilter
        }
        return loadedGroups[0]?.id ?? ''
      })
    } catch (error) {
      setErrorText(toUiErrorText(error))
    } finally {
      setIsGroupsLoading(false)
    }
  }

  useEffect(() => {
    if (!accessToken) {
      setGroups([])
      setPlaylists([])
      setPlaylistTracks([])
      setDraftGroupFilter('')
      setAppliedGroupFilter('')
      setSelectedPlaylistId(null)
      return
    }
    void syncGroups(accessToken)
  }, [accessToken])

  useEffect(() => {
    if (!accessToken || groups.length === 0) {
      setPlaylists([])
      setPlaylistTracks([])
      setSelectedPlaylistId(null)
      setActualRole(null)
      return
    }

    let isMounted = true
    const loadData = async () => {
      setIsDataLoading(true)
      setErrorText(null)
      try {
        const targetGroups = appliedGroupId ? groups.filter((group) => group.id === appliedGroupId) : groups

        const loadedByGroup = await Promise.all(
          targetGroups.map(async (group) => {
            const [nextPlaylists, users] = await Promise.all([
              getGroupPlaylists(accessToken, group.id),
              getGroupUsers(accessToken, group.id),
            ])
            const currentUser = users.find((member) => normalizeEmail(member.email) === sessionEmail) ?? null
            return {
              role: currentUser?.role ?? null,
              playlists: nextPlaylists,
            }
          }),
        )

        if (!isMounted) {
          return
        }

        if (appliedGroupId) {
          setActualRole(loadedByGroup[0]?.role ?? null)
        } else {
          setActualRole(null)
        }

        const roleFilteredGroups =
          appliedRoleFilter === 'ALL'
            ? loadedByGroup
            : loadedByGroup.filter((item) => item.role === appliedRoleFilter)

        const mergedPlaylists = roleFilteredGroups.flatMap((item) => item.playlists)
        setPlaylists(mergedPlaylists)
      } catch (error) {
        if (!isMounted) {
          return
        }
        setPlaylists([])
        setPlaylistTracks([])
        setActualRole(null)
        setErrorText(toUiErrorText(error))
      } finally {
        if (isMounted) {
          setIsDataLoading(false)
        }
      }
    }

    void loadData()
    return () => {
      isMounted = false
    }
  }, [accessToken, groups, appliedGroupId, appliedRoleFilter, sessionEmail])

  useEffect(() => {
    if (isCreateMode) {
      setIsEditMode(false)
    }
  }, [isCreateMode])

  useEffect(() => {
    if (!createImageFile) {
      setCreateImagePreviewUrl(null)
      return
    }
    const objectUrl = URL.createObjectURL(createImageFile)
    setCreateImagePreviewUrl(objectUrl)
    return () => {
      URL.revokeObjectURL(objectUrl)
    }
  }, [createImageFile])

  useEffect(() => {
    if (!editImageFile) {
      setEditImagePreviewUrl(null)
      return
    }
    const objectUrl = URL.createObjectURL(editImageFile)
    setEditImagePreviewUrl(objectUrl)
    return () => {
      URL.revokeObjectURL(objectUrl)
    }
  }, [editImageFile])

  useEffect(() => {
    if (!selectedPlaylistId) {
      setPlaylistTracks([])
      setIsTracksLoading(false)
      setOpenTrackMenuKey(null)
      return
    }
    if (!playlists.some((playlist) => playlist.id === selectedPlaylistId)) {
      setSelectedPlaylistId(null)
      setPlaylistTracks([])
      setIsTracksLoading(false)
      setOpenTrackMenuKey(null)
    }
  }, [playlists, selectedPlaylistId])

  useEffect(() => {
    if (!accessToken || !appliedGroupId || !selectedPlaylistId) {
      setPlaylistTracks([])
      setIsTracksLoading(false)
      setOpenTrackMenuKey(null)
      return
    }

    let isMounted = true
    const loadPlaylistTracks = async () => {
      setIsTracksLoading(true)
      setOpenTrackMenuKey(null)
      try {
        const nextTracks = await getPlaylistTracks(accessToken, appliedGroupId, selectedPlaylistId)
        if (!isMounted) {
          return
        }
        setPlaylistTracks(nextTracks)
      } catch (error) {
        if (!isMounted) {
          return
        }
        setPlaylistTracks([])
        setErrorText(toUiErrorText(error))
      } finally {
        if (isMounted) {
          setIsTracksLoading(false)
        }
      }
    }

    void loadPlaylistTracks()
    return () => {
      isMounted = false
    }
  }, [accessToken, appliedGroupId, selectedPlaylistId])

  const resetCreateForm = () => {
    setCreateName('')
    setCreateImageFile(null)
    setIsCreateMode(false)
  }

  const handleCreateImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0]
    setCreateImageFile(nextFile ?? null)
    event.target.value = ''
  }

  const handleEditImageUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0]
    setEditImageFile(nextFile ?? null)
    event.target.value = ''
  }

  const handleApplyFilters = () => {
    if (!canApplyFilters) {
      return
    }
    setAppliedGroupFilter(draftGroupFilter)
    setAppliedRoleFilter(draftRoleFilter)
    setSelectedPlaylistId(null)
    setIsCreateMode(false)
    setIsEditMode(false)
    setEditImageFile(null)
    setConfirmDialog(null)
    setOpenTrackMenuKey(null)
    setTrackInfoModal(null)
    setIsGroupDropdownOpen(false)
    setIsRoleDropdownOpen(false)
    setErrorText(null)
  }

  const handleCreatePlaylist = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!accessToken || !appliedGroupId) {
      return
    }

    const trimmedName = createName.trim()
    if (trimmedName.length === 0) {
      setErrorText('Введите название плейлиста.')
      return
    }

    setIsSubmitting(true)
    setErrorText(null)
    try {
      const createdPlaylist = await createPlaylist(accessToken, appliedGroupId, {
        name: trimmedName,
        image_url: null,
      })
      const playlistWithImage = createImageFile
        ? await uploadPlaylistImage(accessToken, appliedGroupId, createdPlaylist.id, createImageFile)
        : createdPlaylist

      const nextPlaylist: GroupPlaylistItem = {
        ...playlistWithImage,
        track_count: 0,
      }
      setPlaylists((previous) => [...previous, nextPlaylist])
      setSelectedPlaylistId(nextPlaylist.id)
      resetCreateForm()
    } catch (error) {
      setErrorText(toUiErrorText(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleStartEdit = () => {
    if (!selectedPlaylist) {
      return
    }
    setEditName(selectedPlaylist.name)
    setEditImageFile(null)
    setIsEditMode(true)
    setIsCreateMode(false)
    setErrorText(null)
  }

  const handleSaveEdit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!selectedPlaylist || !accessToken || !appliedGroupId) {
      return
    }

    const nextName = editName.trim()
    if (nextName.length === 0) {
      setErrorText('Название плейлиста не может быть пустым.')
      return
    }

    setIsSubmitting(true)
    setErrorText(null)
    try {
      let nextImageUrl = selectedPlaylist.image_url

      if (nextName !== selectedPlaylist.name) {
        const updatedPlaylist = await updatePlaylist(accessToken, appliedGroupId, selectedPlaylist.id, {
          name: nextName,
        })
        nextImageUrl = updatedPlaylist.image_url
      }

      if (editImageFile) {
        const updatedWithImage = await uploadPlaylistImage(accessToken, appliedGroupId, selectedPlaylist.id, editImageFile)
        nextImageUrl = updatedWithImage.image_url
      }

      setPlaylists((previous) =>
        previous.map((playlist) =>
          playlist.id === selectedPlaylist.id
            ? {
                ...playlist,
                name: nextName,
                image_url: nextImageUrl,
              }
            : playlist,
        ),
      )
      setIsEditMode(false)
      setEditImageFile(null)
      setErrorText(null)
    } catch (error) {
      setErrorText(toUiErrorText(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleOpenCreateMode = () => {
    if (!canManageGroupPlaylists) {
      return
    }
    setIsCreateMode(true)
    setIsEditMode(false)
    setConfirmDialog(null)
    setOpenTrackMenuKey(null)
    setTrackInfoModal(null)
    setErrorText(null)
  }

  const handleOpenAddTracksScreen = () => {
    if (!canManageGroupPlaylists || !selectedPlaylist || !appliedGroupId) {
      return
    }
    navigate('/app/search', {
      state: {
        groupId: appliedGroupId,
        groupName: appliedGroup?.name ?? routeState?.groupName ?? null,
        groupImageUrl: appliedGroup?.image_url ?? routeState?.groupImageUrl ?? null,
        playlistId: selectedPlaylist.id,
        playlistName: selectedPlaylist.name,
      },
    })
  }

  const handlePlaySelectedPlaylist = async () => {
    if (!selectedPlaylist || !accessToken || !appliedGroupId || isPlaybackLoading) {
      return
    }

    setIsPlaybackLoading(true)
    setErrorText(null)

    try {
      const playbackQueueResponse = await getPlaylistPlaybackQueue(accessToken, appliedGroupId, selectedPlaylist.id)
      const playbackQueue = playbackQueueResponse.items.map((item) => ({
        id: String(item.track_id),
        title: item.title,
        artist: item.artist,
        coverUrl: item.cover_url,
        audioUrl: item.audio_url,
      }))
      const firstTrack = playbackQueue[0]
      if (!firstTrack) {
        setErrorText('В этом плейлисте пока нет доступных треков для воспроизведения.')
        return
      }

      const bufferedAudio = new Audio(firstTrack.audioUrl)
      bufferedAudio.preload = 'auto'
      bufferedAudio.load()

      await waitForBufferedPlayback(
        bufferedAudio,
        PLAYBACK_BUFFER_THRESHOLD,
        PLAYBACK_BUFFER_TIMEOUT_MS,
      )

      playTrack(
        {
          id: firstTrack.id,
          title: firstTrack.title,
          artist: firstTrack.artist,
          coverUrl: firstTrack.coverUrl,
          audioUrl: firstTrack.audioUrl,
        },
        {
          audio: bufferedAudio,
          queue: playbackQueue,
          startIndex: 0,
        },
      )
    } catch (error) {
      if (error instanceof Error && error.message === 'AUDIO_BUFFERING_TIMEOUT') {
        setErrorText('Не удалось дождаться буфера трека. Попробуйте еще раз.')
        return
      }
      if (error instanceof Error && error.message === 'AUDIO_BUFFERING_FAILED') {
        setErrorText('Не удалось подготовить трек к воспроизведению.')
        return
      }
      setErrorText(toUiErrorText(error))
    } finally {
      setIsPlaybackLoading(false)
    }
  }

  const handleRequestDeletePlaylist = () => {
    if (!selectedPlaylist) {
      return
    }
    setConfirmDialog({
      type: 'delete-playlist',
      playlistId: selectedPlaylist.id,
      playlistName: selectedPlaylist.name,
    })
  }

  const handleConfirmDeletePlaylist = async () => {
    if (!confirmDialog || !accessToken || !appliedGroupId) {
      return
    }

    setIsConfirmSubmitting(true)
    setErrorText(null)
    try {
      await deletePlaylist(accessToken, appliedGroupId, confirmDialog.playlistId)
      setPlaylists((previous) => previous.filter((playlist) => playlist.id !== confirmDialog.playlistId))
      setPlaylistTracks([])
      setSelectedPlaylistId(null)
      setIsEditMode(false)
      setIsCreateMode(false)
      setConfirmDialog(null)
      setOpenTrackMenuKey(null)
    } catch (error) {
      setErrorText(toUiErrorText(error))
    } finally {
      setIsConfirmSubmitting(false)
    }
  }

  const handleOpenTrackInfo = (track: PlaylistTrackItem) => {
    setTrackInfoModal(track)
    setOpenTrackMenuKey(null)
  }

  const handleTrackMenuToggle = (track: PlaylistTrackItem) => {
    const trackKey = toTrackMenuKey(track)
    setOpenTrackMenuKey((previous) => (previous === trackKey ? null : trackKey))
  }

  const handleRemoveTrackFromPlaylist = async (track: PlaylistTrackItem) => {
    if (!canEditTracks || !accessToken || !appliedGroupId || !selectedPlaylistId) {
      return
    }

    setIsTrackActionLoading(true)
    setErrorText(null)
    try {
      await removeTrackFromPlaylist(
        accessToken,
        appliedGroupId,
        selectedPlaylistId,
        track.track_id,
      )
      setPlaylistTracks((previous) => previous.filter((item) => item.track_id !== track.track_id))
      setPlaylists((previous) =>
        previous.map((playlist) => {
          if (playlist.id !== selectedPlaylistId) {
            return playlist
          }
          return {
            ...playlist,
            track_count: Math.max(0, playlist.track_count - 1),
          }
        }),
      )
      setOpenTrackMenuKey(null)
    } catch (error) {
      setErrorText(toUiErrorText(error))
    } finally {
      setIsTrackActionLoading(false)
    }
  }

  const renderCreateForm = () => (
    <form className={styles.inlineForm} onSubmit={handleCreatePlaylist}>
      <h4 className={styles.inlineFormTitle}>Создать плейлист</h4>
      <div className={styles.createHeader}>
        <span aria-hidden className={styles.createAvatarPreview} style={createImagePreviewStyle} />
        <div className={styles.imageUploadBlock}>
          <label className={styles.uploadButton}>
            Загрузить картинку
            <input
              accept="image/jpeg,image/jpg,image/png,image/webp"
              className={styles.hiddenFileInput}
              onChange={handleCreateImageUpload}
              type="file"
            />
          </label>
          {createImageLabel ? <p className={styles.imageUploadText}>{createImageLabel}</p> : null}
        </div>
      </div>

      <label className={styles.fieldLabel} htmlFor="playlist-create-name">
        Название
      </label>
      <input
        className={styles.textField}
        id="playlist-create-name"
        onChange={(event) => setCreateName(event.target.value)}
        placeholder="Введите название плейлиста"
        value={createName}
      />

      <div className={styles.inlineFormActions}>
        <button className={styles.primaryButton} disabled={isSubmitting} type="submit">
          {isSubmitting ? 'Создаем...' : 'Создать'}
        </button>
        <button className={styles.secondaryButton} onClick={resetCreateForm} type="button">
          Отмена
        </button>
      </div>
    </form>
  )

  return (
    <section className={styles.root}>
      <header className={styles.hero} style={heroStyle}>
        <div className={styles.heroContent}>
          <div className={styles.heroGroup}>
            <span aria-hidden className={styles.heroGroupAvatar} style={heroAvatarStyle} />
            <h2 className={styles.heroGroupTitle}>{appliedGroupLabel}</h2>
          </div>
          <p className={styles.heroRole}>{roleFilterLabel[displayRole]}</p>
        </div>
      </header>

      <section className={styles.filterPanelWrap}>
        <button
          aria-controls="playlist-filters-panel"
          aria-expanded={isFilterPanelOpen}
          className={styles.filterPanelToggle}
          onClick={() => {
            setIsFilterPanelOpen((previous) => !previous)
            setIsGroupDropdownOpen(false)
            setIsRoleDropdownOpen(false)
          }}
          type="button"
        >
          {isFilterPanelOpen ? 'Скрыть фильтры' : 'Показать фильтры'}
        </button>

        {isFilterPanelOpen ? (
          <div className={styles.filterPanel} id="playlist-filters-panel">
            <div className={styles.heroFilters}>
              <div className={styles.dropdownWrap}>
                <button
                  aria-expanded={isGroupDropdownOpen}
                  className={styles.dropdownTrigger}
                  onClick={() => {
                    setIsGroupDropdownOpen((previous) => !previous)
                    setIsRoleDropdownOpen(false)
                  }}
                  type="button"
                >
                  {draftGroupLabel}
                  <span className={styles.chevron}>▼</span>
                </button>

                {isGroupDropdownOpen ? (
                  <div className={styles.dropdownMenu}>
                    <button
                      className={
                        draftGroupFilter === ALL_GROUPS_FILTER
                          ? `${styles.dropdownItem} ${styles.dropdownItemActive}`
                          : styles.dropdownItem
                      }
                      onClick={() => {
                        setDraftGroupFilter(ALL_GROUPS_FILTER)
                        setIsGroupDropdownOpen(false)
                      }}
                      type="button"
                    >
                      Все группы
                    </button>
                    {groups.map((group) => (
                      <button
                        className={
                          draftGroupFilter === group.id
                            ? `${styles.dropdownItem} ${styles.dropdownItemActive}`
                            : styles.dropdownItem
                        }
                        key={group.id}
                        onClick={() => {
                          setDraftGroupFilter(group.id)
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
                  aria-expanded={isRoleDropdownOpen}
                  className={styles.dropdownTrigger}
                  onClick={() => {
                    setIsRoleDropdownOpen((previous) => !previous)
                    setIsGroupDropdownOpen(false)
                  }}
                  type="button"
                >
                  {draftRoleLabel}
                  <span className={styles.chevron}>▼</span>
                </button>

                {isRoleDropdownOpen ? (
                  <div className={styles.dropdownMenu}>
                    {(['ALL', 'MAINTAINER', 'GUEST', 'VIEWER'] as RoleFilter[]).map((role) => (
                      <button
                        className={
                          draftRoleFilter === role
                            ? `${styles.dropdownItem} ${styles.dropdownItemActive}`
                            : styles.dropdownItem
                        }
                        key={role}
                        onClick={() => {
                          setDraftRoleFilter(role)
                          setIsRoleDropdownOpen(false)
                        }}
                        type="button"
                      >
                        {roleFilterLabel[role]}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>

              {hasPendingFilterChanges ? (
                <button
                  className={styles.applyButton}
                  disabled={!canApplyFilters}
                  onClick={handleApplyFilters}
                  type="button"
                >
                  Применить
                </button>
              ) : null}
            </div>
          </div>
        ) : null}
      </section>

      {errorText ? <p className={styles.errorText}>{errorText}</p> : null}
      {roleFilterMismatch ? <p className={styles.hintText}>Для выбранного фильтра роли данных нет.</p> : null}

      <div className={styles.layout}>
        <section className={styles.listColumn}>
          <header className={styles.columnHeader}>
            <h3 className={styles.columnTitle}>Плейлисты</h3>
            {canManageGroupPlaylists ? (
              <button
                aria-label="Создать плейлист"
                className={styles.columnCreateButton}
                onClick={handleOpenCreateMode}
                type="button"
              >
                +
              </button>
            ) : null}
          </header>

          <div className={styles.playlistList}>
            {isGroupsLoading || isDataLoading ? <p className={styles.emptyState}>Загружаем плейлисты...</p> : null}
            {!isGroupsLoading && !isDataLoading && playlists.length === 0 ? (
              <p className={styles.emptyState}>Плейлистов пока нет.</p>
            ) : null}
            {!isDataLoading
              ? playlists.map((playlist) => (
                  <button
                    className={
                      selectedPlaylistId === playlist.id
                        ? `${styles.playlistCard} ${styles.playlistCardActive}`
                        : styles.playlistCard
                    }
                    key={playlist.id}
                    onClick={() => {
                      setSelectedPlaylistId(playlist.id)
                      setIsCreateMode(false)
                      setIsEditMode(false)
                      setOpenTrackMenuKey(null)
                    }}
                    type="button"
                  >
                    <span
                      aria-hidden
                      className={styles.playlistCardAvatar}
                      style={playlist.image_url ? { backgroundImage: `url(${playlist.image_url})` } : undefined}
                    />
                    <span className={styles.playlistCardName}>{playlist.name}</span>
                  </button>
                ))
              : null}
          </div>
        </section>

        <section className={styles.detailsColumn}>
          {isCreateMode ? (
            renderCreateForm()
          ) : (
            <>
              <article
                className={
                  selectedPlaylist
                    ? styles.playlistCardMain
                    : `${styles.playlistCardMain} ${styles.playlistCardMainEmpty}`
                }
              >
                {selectedPlaylist ? (
                  <>
                    <div
                      aria-hidden
                      className={styles.mainCover}
                      style={selectedPlaylist.image_url ? { backgroundImage: `url(${selectedPlaylist.image_url})` } : undefined}
                    />

                    <div className={styles.mainMeta}>
                      <div className={styles.mainTitleRow}>
                        <h3 className={styles.mainTitle} title={selectedPlaylist.name}>
                          {selectedPlaylist.name}
                        </h3>
                        {canManageSelectedPlaylist ? (
                          <button className={styles.iconButton} onClick={handleStartEdit} type="button">
                            ✎
                          </button>
                        ) : null}
                      </div>

                      <div className={styles.mainActions}>
                        <button
                          className={styles.circleAction}
                          disabled={!canPlaySelectedPlaylist}
                          onClick={() => void handlePlaySelectedPlaylist()}
                          type="button"
                        >
                          ▶
                          <span>Слушать</span>
                        </button>
                        <button className={styles.circleAction} type="button">
                          ♡
                          <span>В избранном</span>
                        </button>
                      </div>
                    </div>

                    {canManageSelectedPlaylist ? (
                      <button className={styles.plusButton} onClick={handleOpenAddTracksScreen} type="button">
                        +
                      </button>
                    ) : null}
                  </>
                ) : (
                  <h3 className={styles.mainTitle}>Плейлист не выбран</h3>
                )}
              </article>

              {isEditMode && selectedPlaylist ? (
                <form className={styles.inlineForm} onSubmit={handleSaveEdit}>
                  <h4 className={styles.inlineFormTitle}>Редактировать плейлист</h4>
                  <label className={styles.fieldLabel} htmlFor="playlist-edit-name">
                    Название
                  </label>
                  <input
                    className={styles.textField}
                    id="playlist-edit-name"
                    onChange={(event) => setEditName(event.target.value)}
                    value={editName}
                  />

                  <div className={styles.createHeader}>
                    <span aria-hidden className={styles.createAvatarPreview} style={editImagePreviewStyle} />
                    <div className={styles.imageUploadBlock}>
                      <label className={styles.uploadButton}>
                        Загрузить картинку
                        <input
                          accept="image/jpeg,image/jpg,image/png,image/webp"
                          className={styles.hiddenFileInput}
                          onChange={handleEditImageUpload}
                          type="file"
                        />
                      </label>
                      {editImageLabel ? <p className={styles.imageUploadText}>{editImageLabel}</p> : null}
                    </div>
                  </div>

                  <div className={styles.inlineFormActions}>
                    <button className={styles.primaryButton} disabled={isSubmitting} type="submit">
                      {isSubmitting ? 'Сохраняем...' : 'Сохранить'}
                    </button>
                    <button
                      className={styles.secondaryButton}
                      onClick={() => {
                        setIsEditMode(false)
                        setEditImageFile(null)
                      }}
                      type="button"
                    >
                      Отмена
                    </button>
                  </div>
                </form>
              ) : null}

              <section className={styles.tracksCard}>
                {!selectedPlaylist ? (
                  <p className={styles.emptyState}>Выберите плейлист, чтобы увидеть треки.</p>
                ) : isTracksLoading ? (
                  <p className={styles.emptyState}>Загружаем треки...</p>
                ) : playlistTracks.length === 0 ? (
                  <p className={styles.emptyState}>Пока пусто!</p>
                ) : (
                  playlistTracks.map((track) => {
                    const trackKey = toTrackMenuKey(track)
                    const isMenuOpen = openTrackMenuKey === trackKey
                    const serviceMeta = resolveTrackServiceMeta(track.service)
                    return (
                      <article
                        className={styles.trackRow}
                        key={trackKey}
                      >
                        <span
                          aria-hidden
                          className={styles.trackAvatar}
                          style={track.cover_url ? { backgroundImage: `url(${track.cover_url})` } : undefined}
                        />
                        <div className={styles.trackMeta}>
                          <p className={styles.trackTitle}>{track.title}</p>
                          <p className={styles.trackArtist}>{track.artist}</p>
                        </div>
                        <span className={styles.trackServiceBadge}>{serviceMeta.short}</span>
                        <div className={styles.trackMenuWrap}>
                          <button className={styles.trackMenuButton} onClick={() => handleTrackMenuToggle(track)} type="button">
                            ...
                          </button>
                          {isMenuOpen ? (
                            <div className={styles.trackMenuPopup}>
                              <button
                                className={styles.trackMenuItem}
                                onClick={() => handleOpenTrackInfo(track)}
                                type="button"
                              >
                                О треке
                              </button>
                              {canEditTracks ? (
                                <button
                                  className={styles.trackMenuItemDanger}
                                  disabled={isTrackActionLoading}
                                  onClick={() => void handleRemoveTrackFromPlaylist(track)}
                                  type="button"
                                >
                                  {isTrackActionLoading ? 'Удаляем...' : 'Удалить трек'}
                                </button>
                              ) : null}
                            </div>
                          ) : null}
                        </div>
                      </article>
                    )
                  })
                )}
              </section>

              {canManageSelectedPlaylist ? (
                <button className={styles.deleteButton} onClick={handleRequestDeletePlaylist} type="button">
                  Удалить плейлист
                </button>
              ) : null}
            </>
          )}
        </section>
      </div>

      {trackInfoModal ? (
        <div aria-modal="true" className={styles.modalOverlay} onClick={() => setTrackInfoModal(null)} role="dialog">
          <div className={styles.modalCard} onClick={(event) => event.stopPropagation()}>
            <span
              aria-hidden
              className={styles.modalTrackCover}
              style={trackInfoModal.cover_url ? { backgroundImage: `url(${trackInfoModal.cover_url})` } : undefined}
            />
            <h3 className={styles.modalTitle}>О треке</h3>
            <p className={styles.modalText}><strong>Название:</strong> {trackInfoModal.title}</p>
            <p className={styles.modalText}><strong>Исполнитель:</strong> {trackInfoModal.artist}</p>
            <p className={styles.modalText}><strong>Сервис:</strong> {resolveTrackServiceMeta(trackInfoModal.service).full}</p>
            {resolveTrackServiceUrl(trackInfoModal) ? (
              <p className={styles.modalText}>
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
            <div className={styles.modalActions}>
              <button className={styles.secondaryButton} onClick={() => setTrackInfoModal(null)} type="button">
                Закрыть
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {confirmDialog ? (
        <div aria-modal="true" className={styles.modalOverlay} onClick={() => setConfirmDialog(null)} role="dialog">
          <div className={styles.modalCard} onClick={(event) => event.stopPropagation()}>
            <h3 className={styles.modalTitle}>Подтвердите удаление</h3>
            <p className={styles.modalText}>
              Удалить плейлист "{confirmDialog.playlistName}"? Это действие нельзя отменить.
            </p>
            <div className={styles.modalActions}>
              <button
                className={styles.modalDangerButton}
                disabled={isConfirmSubmitting}
                onClick={() => void handleConfirmDeletePlaylist()}
                type="button"
              >
                {isConfirmSubmitting ? 'Удаляем...' : 'Удалить'}
              </button>
              <button
                className={styles.secondaryButton}
                disabled={isConfirmSubmitting}
                onClick={() => setConfirmDialog(null)}
                type="button"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}
