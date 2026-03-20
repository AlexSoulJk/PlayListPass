import { startTransition, useEffect, useState, type ChangeEvent, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../../../../app/providers/useAuth'
import {
  changeGroupUserRole,
  createGroup,
  deleteGroup,
  getGroupList,
  getGroupPlaylists,
  getGroupQr,
  getGroupUsers,
  GroupsApiError,
  updateGroupInfo,
} from '../../../../groups/api/groupsApi'
import type {
  GroupListItem,
  GroupMutableRole,
  GroupPlaylistItem,
  GroupQrResponse,
  GroupRole,
  GroupUserItem,
} from '../../../../groups/models/types'
import styles from './GroupsWorkspacePage.module.css'

const roleLabel: Record<GroupRole, string> = {
  MAINTAINER: 'host',
  GUEST: 'guest',
  VIEWER: 'viewer',
}

const sortGroupsByName = (groups: GroupListItem[]): GroupListItem[] => {
  return [...groups].sort((left, right) => left.name.localeCompare(right.name, 'ru-RU'))
}

const toUiErrorText = (error: unknown): string => {
  if (!(error instanceof GroupsApiError)) {
    return 'Произошла непредвиденная ошибка. Повторите попытку.'
  }

  switch (error.code) {
    case 'UNAUTHORIZED':
      return 'Сессия истекла. Авторизуйтесь повторно.'
    case 'GROUP_NOT_FOUND':
      return 'Группа не найдена. Обновите список.'
    case 'ACCESS_DENIED':
      return 'Нет доступа к этой группе.'
    case 'MAINTAINER_REQUIRED':
      return 'Только host может выполнять это действие.'
    case 'GROUP_NAME_ALREADY_EXISTS':
      return 'Группа с таким названием уже существует.'
    case 'GROUP_USER_NOT_FOUND':
      return 'Участник не найден в выбранной группе.'
    case 'CANNOT_CHANGE_MAINTAINER_ROLE':
      return 'Нельзя изменить роль host.'
    case 'VALIDATION_ERROR':
      return 'Проверьте корректность данных формы.'
    case 'NETWORK_ERROR':
      return 'Сеть недоступна или backend не отвечает.'
    default:
      return error.message
  }
}

const getNextMutableRole = (role: GroupRole): GroupMutableRole | null => {
  if (role === 'GUEST') {
    return 'VIEWER'
  }
  if (role === 'VIEWER') {
    return 'GUEST'
  }
  return null
}

const roleChangeLabel: Record<GroupMutableRole, string> = {
  GUEST: 'Сделать guest',
  VIEWER: 'Сделать viewer',
}

export function GroupsWorkspacePage() {
  const navigate = useNavigate()
  const { session } = useAuth()

  const [groups, setGroups] = useState<GroupListItem[]>([])
  const [activeGroupId, setActiveGroupId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isEditMode, setIsEditMode] = useState(false)

  const [groupUsers, setGroupUsers] = useState<GroupUserItem[]>([])
  const [groupPlaylists, setGroupPlaylists] = useState<GroupPlaylistItem[]>([])
  const [groupQr, setGroupQr] = useState<GroupQrResponse | null>(null)
  const [isQrModalOpen, setIsQrModalOpen] = useState(false)

  const [createName, setCreateName] = useState('')
  const [renameValue, setRenameValue] = useState('')
  const [pendingImageName, setPendingImageName] = useState<string | null>(null)
  const [loadingGroups, setLoadingGroups] = useState(false)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [pendingRoleUserId, setPendingRoleUserId] = useState<string | null>(null)
  const [errorText, setErrorText] = useState<string | null>(null)

  const accessToken = session?.accessToken ?? null
  const activeGroup = groups.find((group) => group.id === activeGroupId) ?? null
  const currentUser = groupUsers.find((member) => member.email === session?.email) ?? null
  const canManageGroup = currentUser?.role === 'MAINTAINER'

  const syncGroupList = async (
    token: string,
    preferredGroupId: string | null = null,
  ): Promise<void> => {
    setLoadingGroups(true)
    setErrorText(null)
    try {
      const loadedGroups = await getGroupList(token)
      startTransition(() => {
        setGroups(loadedGroups)
        setActiveGroupId((previousGroupId) => {
          const targetGroupId = preferredGroupId ?? previousGroupId
          if (targetGroupId && loadedGroups.some((group) => group.id === targetGroupId)) {
            return targetGroupId
          }
          return loadedGroups[0]?.id ?? null
        })
      })
    } catch (error) {
      setErrorText(toUiErrorText(error))
    } finally {
      setLoadingGroups(false)
    }
  }

  useEffect(() => {
    if (!accessToken) {
      setGroups([])
      setActiveGroupId(null)
      setIsCreating(false)
      setIsEditMode(false)
      setGroupUsers([])
      setGroupPlaylists([])
      setGroupQr(null)
      setIsQrModalOpen(false)
      return
    }

    void syncGroupList(accessToken)
  }, [accessToken])

  useEffect(() => {
    if (!activeGroupId) {
      setRenameValue('')
      return
    }
    const selectedGroup = groups.find((group) => group.id === activeGroupId)
    setRenameValue(selectedGroup?.name ?? '')
  }, [activeGroupId, groups])

  useEffect(() => {
    if (!accessToken || !activeGroupId || isCreating) {
      setGroupUsers([])
      setGroupPlaylists([])
      setGroupQr(null)
      return
    }

    let isMounted = true

    const loadGroupDetails = async () => {
      setLoadingDetails(true)
      setErrorText(null)
      try {
        const [users, playlists, qr] = await Promise.all([
          getGroupUsers(accessToken, activeGroupId),
          getGroupPlaylists(accessToken, activeGroupId),
          getGroupQr(accessToken, activeGroupId),
        ])
        if (!isMounted) {
          return
        }
        startTransition(() => {
          setGroupUsers(users)
          setGroupPlaylists(playlists)
          setGroupQr(qr)
        })
      } catch (error) {
        if (!isMounted) {
          return
        }
        setGroupUsers([])
        setGroupPlaylists([])
        setGroupQr(null)
        setErrorText(toUiErrorText(error))
      } finally {
        if (isMounted) {
          setLoadingDetails(false)
        }
      }
    }

    void loadGroupDetails()

    return () => {
      isMounted = false
    }
  }, [accessToken, activeGroupId, isCreating])

  const handleOpenCreateMode = () => {
    setIsCreating(true)
    setIsEditMode(true)
    setActiveGroupId(null)
    setCreateName('')
    setRenameValue('')
    setPendingImageName(null)
    setGroupUsers([])
    setGroupPlaylists([])
    setGroupQr(null)
    setErrorText(null)
  }

  const handleCreateGroup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!accessToken) {
      return
    }

    const nextName = createName.trim()
    if (nextName.length === 0) {
      setErrorText('Введите название группы перед созданием.')
      return
    }

    setIsSubmitting(true)
    setErrorText(null)
    try {
      const createdGroup = await createGroup(accessToken, {
        name: nextName,
        is_public: true,
      })
      setCreateName('')
      setPendingImageName(null)
      setIsCreating(false)
      setIsEditMode(false)
      await syncGroupList(accessToken, createdGroup.id)
    } catch (error) {
      setErrorText(toUiErrorText(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleUpdateGroup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!accessToken || !activeGroup || !canManageGroup || !isEditMode) {
      return
    }

    const nextName = renameValue.trim()
    if (nextName.length === 0) {
      setErrorText('Название группы не может быть пустым.')
      return
    }

    setIsSubmitting(true)
    setErrorText(null)
    try {
      const updatedGroup = await updateGroupInfo(accessToken, activeGroup.id, {
        name: nextName,
      })
      startTransition(() => {
        setGroups((previousGroups) => {
          return sortGroupsByName(
            previousGroups.map((group) => (group.id === updatedGroup.id ? updatedGroup : group)),
          )
        })
      })
      setRenameValue(updatedGroup.name)
      setIsEditMode(false)
      setPendingImageName(null)
    } catch (error) {
      setErrorText(toUiErrorText(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleToggleEditMode = () => {
    if (!canManageGroup) {
      return
    }
    setIsEditMode((previous) => !previous)
    setPendingImageName(null)
    setErrorText(null)
  }

  const handleDeleteGroup = async () => {
    if (!accessToken || !activeGroup || !canManageGroup || !isEditMode) {
      return
    }

    const confirmed = window.confirm(`Удалить группу "${activeGroup.name}"?`)
    if (!confirmed) {
      return
    }

    setIsSubmitting(true)
    setErrorText(null)
    try {
      await deleteGroup(accessToken, activeGroup.id)
      setIsEditMode(false)
      await syncGroupList(accessToken, null)
    } catch (error) {
      setErrorText(toUiErrorText(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleChangeMemberRole = async (userId: string, role: GroupMutableRole) => {
    if (!accessToken || !activeGroupId || !canManageGroup || !isEditMode) {
      return
    }

    setPendingRoleUserId(userId)
    setErrorText(null)
    try {
      const updatedMember = await changeGroupUserRole(accessToken, activeGroupId, userId, role)
      startTransition(() => {
        setGroupUsers((previousMembers) => {
          return previousMembers.map((member) => (member.id === updatedMember.id ? updatedMember : member))
        })
      })
    } catch (error) {
      setErrorText(toUiErrorText(error))
    } finally {
      setPendingRoleUserId(null)
    }
  }

  const handleSelectGroup = (groupId: string) => {
    setIsCreating(false)
    setIsEditMode(false)
    setPendingImageName(null)
    setErrorText(null)
    setActiveGroupId(groupId)
  }

  const handleOpenPlaylists = () => {
    if (!activeGroup) {
      return
    }

    navigate('/app/playlists', {
      state: {
        groupId: activeGroup.id,
        groupName: activeGroup.name,
        playlists: groupPlaylists,
      },
    })
  }

  const handleOpenQrModal = () => {
    if (!groupQr) {
      setErrorText('QR-код еще не загружен. Попробуйте выбрать группу заново.')
      return
    }
    setIsQrModalOpen(true)
  }

  const handleCloseQrModal = () => {
    setIsQrModalOpen(false)
  }

  const handleUploadImageMock = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0]
    setPendingImageName(nextFile ? nextFile.name : null)
  }

  const handleCancelCreate = () => {
    setIsCreating(false)
    setIsEditMode(false)
    setPendingImageName(null)
    setErrorText(null)
    if (accessToken) {
      void syncGroupList(accessToken, groups[0]?.id ?? null)
    }
  }

  const qrExpiryLabel = groupQr ? new Date(groupQr.expired_at).toLocaleString('ru-RU') : '—'
  const groupImageLabel = pendingImageName ? `Файл: ${pendingImageName}` : 'Загрузка изображения (mock)'

  return (
    <section className={styles.root}>
      <section className={styles.groupListSection}>
        <header className={styles.groupListHeader}>
          <h2 className={styles.groupListTitle}>Группы</h2>
          <button
            className={styles.editButton}
            aria-label="Создать новую группу"
            disabled={loadingGroups || isSubmitting || isCreating}
            onClick={handleOpenCreateMode}
            type="button"
          >
            <svg aria-hidden viewBox="0 0 24 24">
              <path d="M12 5V19" />
              <path d="M5 12H19" />
            </svg>
          </button>
        </header>

        {errorText ? <p className={styles.errorText}>{errorText}</p> : null}

        <div className={styles.groupList}>
          {loadingGroups ? <p className={styles.emptyState}>Загружаем группы...</p> : null}
          {!loadingGroups && groups.length === 0 ? (
            <p className={styles.emptyState}>Вы пока не состоите ни в одной группе.</p>
          ) : null}
          {!loadingGroups
            ? groups.map((group) => (
                <button
                  className={
                    group.id === activeGroupId && !isCreating
                      ? `${styles.groupCard} ${styles.groupCardActive}`
                      : styles.groupCard
                  }
                  key={group.id}
                  onClick={() => handleSelectGroup(group.id)}
                  type="button"
                >
                  <span className={styles.avatar} aria-hidden />
                  <span className={styles.groupName}>{group.name}</span>
                </button>
              ))
            : null}
        </div>
      </section>

      <section className={styles.detailsSection}>
        {isCreating ? (
          <>
            <div className={styles.detailsTopBar}>
              <span className={styles.modeBadge}>Создание группы</span>
            </div>

            <form className={styles.createDetailsForm} onSubmit={handleCreateGroup}>
              <div className={styles.detailsHeader}>
                <div className={styles.detailsAvatar} aria-hidden />
                <div className={styles.imageUploadBlock}>
                  <label className={styles.uploadButton}>
                    Загрузить картинку
                    <input className={styles.hiddenFileInput} onChange={handleUploadImageMock} type="file" />
                  </label>
                  <p className={styles.imageUploadText}>{groupImageLabel}</p>
                </div>
              </div>

              <label className={styles.renameLabel} htmlFor="create-group-name-input">
                Название группы
              </label>
              <input
                className={styles.renameInput}
                id="create-group-name-input"
                onChange={(event) => setCreateName(event.target.value)}
                placeholder="Введите название группы"
                value={createName}
              />

              <div className={styles.formActions}>
                <button className={styles.renameButton} disabled={isSubmitting} type="submit">
                  Создать
                </button>
                <button className={styles.secondaryButton} onClick={handleCancelCreate} type="button">
                  Отмена
                </button>
              </div>
            </form>
          </>
        ) : !activeGroup ? (
          <p className={styles.emptyState}>Выберите группу слева, чтобы увидеть детали.</p>
        ) : (
          <>
            <div className={styles.detailsTopBar}>
              <span className={styles.modeBadge}>Информация о группе</span>
              <button
                className={styles.pencilButton}
                disabled={!canManageGroup}
                onClick={handleToggleEditMode}
                type="button"
              >
                <svg aria-hidden viewBox="0 0 24 24">
                  <path d="M4 20L8.5 19L19 8.5L14.5 4L4 14.5L4 20Z" />
                  <path d="M12.8 5.7L17.3 10.2" />
                </svg>
              </button>
            </div>

            <div className={styles.detailsHeader}>
              <div className={styles.detailsAvatar} aria-hidden />
              <div className={styles.imageUploadBlock}>
                {isEditMode && canManageGroup ? (
                  <label className={styles.uploadButton}>
                    Загрузить картинку
                    <input className={styles.hiddenFileInput} onChange={handleUploadImageMock} type="file" />
                  </label>
                ) : null}
                {isEditMode && canManageGroup ? (
                  <p className={styles.imageUploadText}>{groupImageLabel}</p>
                ) : null}
              </div>
              {isEditMode && canManageGroup ? (
                <form className={styles.renameForm} onSubmit={handleUpdateGroup}>
                  <label className={styles.renameLabel} htmlFor="group-name-input">
                    Название группы
                  </label>
                  <div className={styles.renameControls}>
                    <input
                      className={styles.renameInput}
                      disabled={isSubmitting}
                      id="group-name-input"
                      onChange={(event) => setRenameValue(event.target.value)}
                      value={renameValue}
                    />
                    <button className={styles.renameButton} disabled={isSubmitting} type="submit">
                      Сохранить
                    </button>
                  </div>
                </form>
              ) : (
                <h3 className={styles.detailsName}>{activeGroup.name}</h3>
              )}
            </div>

            <div className={styles.linkBlocks}>
              <button className={styles.linkBlock} onClick={handleOpenPlaylists} type="button">
                <span>Плейлисты группы</span>
                <span className={styles.linkArrow}>{groupPlaylists.length}</span>
              </button>
              <button className={styles.linkBlock} onClick={handleOpenQrModal} type="button">
                <span>QR-код группы</span>
                <span className={styles.linkArrow}>{groupQr?.is_expired ? 'expired' : 'open'}</span>
              </button>
            </div>

            <div className={styles.membersCard}>
              {loadingDetails ? <p className={styles.emptyState}>Загружаем участников...</p> : null}
              {!loadingDetails && groupUsers.length === 0 ? (
                <p className={styles.emptyState}>В группе пока нет участников.</p>
              ) : null}
              {!loadingDetails
                ? groupUsers.map((member) => {
                    const nextRole = getNextMutableRole(member.role)
                    const memberName = member.name.trim().length > 0 ? member.name : member.email

                    return (
                      <div className={styles.memberRow} key={member.id}>
                        <span className={styles.memberAvatar} aria-hidden />
                        <span className={styles.memberName}>{memberName}</span>
                        <div className={styles.memberActions}>
                          <span className={styles.memberRole}>{roleLabel[member.role]}</span>
                          {canManageGroup && isEditMode && nextRole ? (
                            <button
                              className={styles.memberRoleButton}
                              disabled={pendingRoleUserId === member.id}
                              onClick={() => void handleChangeMemberRole(member.id, nextRole)}
                              type="button"
                            >
                              {roleChangeLabel[nextRole]}
                            </button>
                          ) : null}
                        </div>
                      </div>
                    )
                  })
                : null}
            </div>

            <button
              className={styles.deleteButton}
              disabled={!canManageGroup || !isEditMode || isSubmitting}
              onClick={handleDeleteGroup}
              type="button"
            >
              Удалить группу
            </button>
          </>
        )}
      </section>

      {isQrModalOpen && groupQr ? (
        <div
          aria-modal="true"
          className={styles.modalOverlay}
          onClick={handleCloseQrModal}
          role="dialog"
        >
          <div className={styles.modalCard} onClick={(event) => event.stopPropagation()}>
            <h3 className={styles.modalTitle}>QR-код группы</h3>
            <p className={styles.modalText}>Ссылка для входа в группу:</p>
            <input className={styles.modalInput} readOnly value={groupQr.qr_url} />
            <p className={styles.modalText}>Истекает: {qrExpiryLabel}</p>
            <div className={styles.modalActions}>
              <a className={styles.modalLinkButton} href={groupQr.qr_url} rel="noreferrer" target="_blank">
                Открыть ссылку
              </a>
              <button className={styles.secondaryButton} onClick={handleCloseQrModal} type="button">
                Закрыть
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}
