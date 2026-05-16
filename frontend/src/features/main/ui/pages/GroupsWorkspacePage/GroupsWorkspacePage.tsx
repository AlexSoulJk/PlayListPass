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
  uploadGroupImage,
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

const mutableRoles: GroupMutableRole[] = ['GUEST', 'VIEWER']

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
    case 'GROUP_IMAGE_UNSUPPORTED_FORMAT':
      return 'Неподдерживаемый формат картинки. Используйте JPG, JPEG, PNG или WEBP.'
    case 'GROUP_IMAGE_OBJECT_NOT_FOUND':
      return 'Файл картинки не найден в хранилище. Попробуйте загрузить снова.'
    case 'GROUP_IMAGE_UPLOAD_FAILED':
      return 'Не удалось загрузить файл картинки. Повторите попытку.'
    case 'STORAGE_BACKEND_NOT_AVAILABLE':
      return 'Сервис хранения временно недоступен. Попробуйте позже.'
    case 'VALIDATION_ERROR':
      return 'Проверьте корректность данных формы.'
    case 'NETWORK_ERROR':
      return 'Сеть недоступна или backend не отвечает.'
    default:
      return error.message
  }
}

const getGroupAvatarStyle = (imageUrl: string | null | undefined) => {
  if (!imageUrl) {
    return undefined
  }

  return {
    backgroundImage: `url(${imageUrl})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
  }
}

const toRoleName = (role: GroupMutableRole): string => {
  return role === 'GUEST' ? 'guest' : 'viewer'
}

const normalizeEmail = (email: string | null | undefined): string => {
  return (email ?? '').trim().toLowerCase()
}

type ConfirmDialogState =
  | {
      type: 'delete-group'
      groupId: string
      groupName: string
    }
  | {
      type: 'change-role'
      memberId: string
      memberName: string
      nextRole: GroupMutableRole
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
  const [pendingImageFile, setPendingImageFile] = useState<File | null>(null)
  const [loadingGroups, setLoadingGroups] = useState(false)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [pendingRoleUserId, setPendingRoleUserId] = useState<string | null>(null)
  const [openedRoleMenuUserId, setOpenedRoleMenuUserId] = useState<string | null>(null)
  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialogState | null>(null)
  const [isConfirmSubmitting, setIsConfirmSubmitting] = useState(false)
  const [errorText, setErrorText] = useState<string | null>(null)

  const accessToken = session?.accessToken ?? null
  const activeGroup = groups.find((group) => group.id === activeGroupId) ?? null
  const sessionEmailNormalized = normalizeEmail(session?.email)
  const currentUser =
    groupUsers.find((member) => normalizeEmail(member.email) === sessionEmailNormalized) ?? null
  const currentUserRole = currentUser?.role ?? null
  const canManageGroup = currentUserRole === 'MAINTAINER'

  const syncGroupList = async (token: string, preferredGroupId: string | null = null): Promise<void> => {
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
      setConfirmDialog(null)
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
    setOpenedRoleMenuUserId(null)
    setActiveGroupId(null)
    setCreateName('')
    setRenameValue('')
    setPendingImageFile(null)
    setGroupUsers([])
    setGroupPlaylists([])
    setGroupQr(null)
    setConfirmDialog(null)
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
      const groupWithImage = pendingImageFile
        ? await uploadGroupImage(accessToken, createdGroup.id, pendingImageFile)
        : createdGroup
      setCreateName('')
      setPendingImageFile(null)
      setIsCreating(false)
      setIsEditMode(false)
      await syncGroupList(accessToken, groupWithImage.id)
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
      const nameChanged = nextName !== activeGroup.name
      let updatedGroup = activeGroup

      if (nameChanged) {
        updatedGroup = await updateGroupInfo(accessToken, activeGroup.id, {
          name: nextName,
        })
      }

      if (pendingImageFile) {
        updatedGroup = await uploadGroupImage(accessToken, activeGroup.id, pendingImageFile)
      }

      startTransition(() => {
        setGroups((previousGroups) => {
          return sortGroupsByName(previousGroups.map((group) => (group.id === updatedGroup.id ? updatedGroup : group)))
        })
      })
      setRenameValue(updatedGroup.name)
      setIsEditMode(false)
      setPendingImageFile(null)
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
    setPendingImageFile(null)
    setOpenedRoleMenuUserId(null)
    setErrorText(null)
  }

  const handleDeleteGroup = () => {
    if (!accessToken || !activeGroup || !canManageGroup) {
      return
    }

    setOpenedRoleMenuUserId(null)
    setConfirmDialog({
      type: 'delete-group',
      groupId: activeGroup.id,
      groupName: activeGroup.name,
    })
  }

  const handleCloseConfirmDialog = () => {
    if (isConfirmSubmitting) {
      return
    }
    setConfirmDialog(null)
  }

  const handleChangeMemberRole = (
    member: GroupUserItem,
    role: GroupMutableRole,
  ) => {
    if (!accessToken || !activeGroupId || !canManageGroup) {
      return
    }

    if (member.role === role) {
      setOpenedRoleMenuUserId(null)
      return
    }

    const memberName = member.name.trim().length > 0 ? member.name : member.email
    setOpenedRoleMenuUserId(null)
    setConfirmDialog({
      type: 'change-role',
      memberId: member.id,
      memberName,
      nextRole: role,
    })
  }

  const handleConfirmDialogAction = async () => {
    const dialog = confirmDialog
    if (!dialog || !accessToken) {
      return
    }

    if (dialog.type === 'change-role' && !activeGroupId) {
      return
    }

    setIsConfirmSubmitting(true)
    setErrorText(null)
    try {
      if (dialog.type === 'delete-group') {
        setIsSubmitting(true)
        await deleteGroup(accessToken, dialog.groupId)
        setIsEditMode(false)
        await syncGroupList(accessToken, null)
      } else {
        setPendingRoleUserId(dialog.memberId)
        const updatedMember = await changeGroupUserRole(
          accessToken,
          activeGroupId!,
          dialog.memberId,
          dialog.nextRole,
        )
        startTransition(() => {
          setGroupUsers((previousMembers) => {
            return previousMembers.map((previousMember) =>
              previousMember.id === updatedMember.id ? updatedMember : previousMember,
            )
          })
        })
      }
      setConfirmDialog(null)
    } catch (error) {
      setErrorText(toUiErrorText(error))
    } finally {
      if (dialog.type === 'delete-group') {
        setIsSubmitting(false)
      } else {
        setPendingRoleUserId(null)
      }
      setIsConfirmSubmitting(false)
    }
  }

  const handleSelectGroup = (groupId: string) => {
    setIsCreating(false)
    setIsEditMode(false)
    setOpenedRoleMenuUserId(null)
    setConfirmDialog(null)
    setPendingImageFile(null)
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
      setErrorText('qr-код группы еще не загружен. Попробуйте выбрать группу заново.')
      return
    }
    setIsQrModalOpen(true)
  }

  const handleCloseQrModal = () => {
    setIsQrModalOpen(false)
  }

  const handleUploadImage = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0]
    setPendingImageFile(nextFile ?? null)
    event.target.value = ''
  }

  const handleCancelCreate = () => {
    setIsCreating(false)
    setIsEditMode(false)
    setPendingImageFile(null)
    setOpenedRoleMenuUserId(null)
    setConfirmDialog(null)
    setErrorText(null)
    if (accessToken) {
      void syncGroupList(accessToken, groups[0]?.id ?? null)
    }
  }

  const isGuest = currentUserRole === 'GUEST'
  const isViewer = currentUserRole === 'VIEWER'
  const isHost = currentUserRole === 'MAINTAINER'
  const groupImageLabel = pendingImageFile ? `Файл: ${pendingImageFile.name}` : ''
  const qrExpiryLabel = groupQr ? new Date(groupQr.expired_at).toLocaleString('ru-RU') : '—'
  const confirmTitle =
    confirmDialog?.type === 'delete-group'
      ? 'Подтвердите удаление группы'
      : 'Подтвердите изменение роли'
  const confirmMessage =
    confirmDialog?.type === 'delete-group'
      ? `Удалить группу "${confirmDialog.groupName}"? Это действие нельзя отменить.`
      : confirmDialog
        ? `Изменить роль участника "${confirmDialog.memberName}" на ${toRoleName(confirmDialog.nextRole)}?`
        : ''
  const confirmActionLabel =
    confirmDialog?.type === 'delete-group' ? 'Удалить группу' : 'Сменить роль'

  return (
    <section className={styles.root}>
      <section className={styles.groupListSection}>
        <header className={styles.groupListHeader}>
          <h2 className={styles.groupListTitle}>Группы</h2>
          <button
            aria-label="Создать новую группу"
            className={styles.editButton}
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
                  <span aria-hidden className={styles.avatar} style={getGroupAvatarStyle(group.image_url)} />
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
                <div aria-hidden className={styles.detailsAvatar} />
                <div className={styles.imageUploadBlock}>
                  <label className={styles.uploadButton}>
                    Загрузить картинку
                    <input
                      accept="image/jpeg,image/jpg,image/png,image/webp"
                      className={styles.hiddenFileInput}
                      onChange={handleUploadImage}
                      type="file"
                    />
                  </label>
                  {groupImageLabel ? <p className={styles.imageUploadText}>{groupImageLabel}</p> : null}
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
              {isHost ? (
                <button className={styles.pencilButton} onClick={handleToggleEditMode} type="button">
                  <svg aria-hidden viewBox="0 0 24 24">
                    <path d="M4 20L8.5 19L19 8.5L14.5 4L4 14.5L4 20Z" />
                    <path d="M12.8 5.7L17.3 10.2" />
                  </svg>
                </button>
              ) : null}
            </div>

            <div className={styles.detailsHeader}>
              <div aria-hidden className={styles.detailsAvatar} style={getGroupAvatarStyle(activeGroup.image_url)} />
              <h3 className={styles.detailsName}>{activeGroup.name}</h3>

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

                  <div className={styles.imageUploadBlock}>
                    <label className={styles.uploadButton}>
                      Загрузить картинку
                      <input
                        accept="image/jpeg,image/jpg,image/png,image/webp"
                        className={styles.hiddenFileInput}
                        onChange={handleUploadImage}
                        type="file"
                      />
                    </label>
                    {groupImageLabel ? <p className={styles.imageUploadText}>{groupImageLabel}</p> : null}
                  </div>
                </form>
              ) : null}
            </div>

            <div className={styles.linkBlocks}>
              <button className={styles.linkBlock} onClick={handleOpenPlaylists} type="button">
                <span>плейлисты группы</span>
                <span className={styles.linkArrow}>›</span>
              </button>
              <button className={styles.linkBlock} onClick={handleOpenQrModal} type="button">
                <span>qr-код группы</span>
                <span className={styles.linkArrow}>›</span>
              </button>
            </div>

            <div className={styles.membersCard}>
              {loadingDetails ? <p className={styles.emptyState}>Загружаем участников...</p> : null}
              {!loadingDetails && groupUsers.length === 0 ? (
                <p className={styles.emptyState}>В группе пока нет участников.</p>
              ) : null}
              {!loadingDetails
                ? groupUsers.map((member) => {
                    const memberName = member.name.trim().length > 0 ? member.name : member.email
                    const isSelf = normalizeEmail(member.email) === sessionEmailNormalized
                    const canShowRoleMenu =
                      canManageGroup && !isSelf && member.role !== 'MAINTAINER'
                    const isRoleMenuOpen = openedRoleMenuUserId === member.id
                    const isRoleUpdating = pendingRoleUserId === member.id

                    return (
                      <div className={styles.memberRow} key={member.id}>
                        <span aria-hidden className={styles.memberAvatar} />
                        <span className={styles.memberName}>{memberName}</span>

                        <div className={styles.memberActions}>
                          <span className={styles.memberRole}>{roleLabel[member.role]}</span>

                          {canShowRoleMenu ? (
                            <div className={styles.roleMenuWrap}>
                              <button
                                aria-expanded={isRoleMenuOpen}
                                aria-label={`Изменить роль участника ${memberName}`}
                                className={styles.roleMenuToggle}
                                disabled={isRoleUpdating}
                                onClick={() =>
                                  setOpenedRoleMenuUserId((previous) => (previous === member.id ? null : member.id))
                                }
                                type="button"
                              >
                                ...
                              </button>

                              {isRoleMenuOpen ? (
                                <div className={styles.roleMenu}>
                                  {mutableRoles.map((role) => {
                                    const isCurrentRole = member.role === role
                                    return (
                                      <button
                                        className={
                                          isCurrentRole
                                            ? `${styles.roleMenuItem} ${styles.roleMenuItemActive}`
                                            : styles.roleMenuItem
                                        }
                                        disabled={isRoleUpdating}
                                        key={role}
                                        onClick={() => void handleChangeMemberRole(member, role)}
                                        type="button"
                                      >
                                        {toRoleName(role)}
                                      </button>
                                    )
                                  })}
                                </div>
                              ) : null}
                            </div>
                          ) : null}
                        </div>
                      </div>
                    )
                  })
                : null}
            </div>

            {isHost ? (
              <button className={styles.deleteButton} disabled={isSubmitting} onClick={handleDeleteGroup} type="button">
                Удалить группу
              </button>
            ) : null}

            {isGuest ? (
              <button className={styles.mockActionButton} disabled type="button">
                Выйти из группы
              </button>
            ) : null}

            {isViewer ? (
              <button className={styles.mockActionButton} disabled type="button">
                Перестать наблюдать
              </button>
            ) : null}
          </>
        )}
      </section>

      {isQrModalOpen && groupQr ? (
        <div aria-modal="true" className={styles.modalOverlay} onClick={handleCloseQrModal} role="dialog">
          <div className={styles.modalCard} onClick={(event) => event.stopPropagation()}>
            <h3 className={styles.modalTitle}>qr-код группы</h3>
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

      {confirmDialog ? (
        <div aria-modal="true" className={styles.modalOverlay} onClick={handleCloseConfirmDialog} role="dialog">
          <div className={styles.modalCard} onClick={(event) => event.stopPropagation()}>
            <h3 className={styles.modalTitle}>{confirmTitle}</h3>
            <p className={styles.modalText}>{confirmMessage}</p>
            <div className={styles.modalActions}>
              <button
                className={styles.modalDangerButton}
                disabled={isConfirmSubmitting}
                onClick={() => void handleConfirmDialogAction()}
                type="button"
              >
                {isConfirmSubmitting ? 'Выполняем...' : confirmActionLabel}
              </button>
              <button
                className={styles.secondaryButton}
                disabled={isConfirmSubmitting}
                onClick={handleCloseConfirmDialog}
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
