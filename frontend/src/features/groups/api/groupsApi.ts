import axios from 'axios'
import { httpClient } from '../../../shared/api/httpClient'
import type {
  GroupCreatePayload,
  GroupDeleteResponse,
  GroupListItem,
  GroupMutableRole,
  GroupPlaylistItem,
  GroupQrResponse,
  GroupUpdatePayload,
  GroupUserItem,
  GroupsErrorCode,
} from '../models/types'

type ErrorPayload = {
  detail?: unknown
}

export class GroupsApiError extends Error {
  code: GroupsErrorCode

  constructor(code: GroupsErrorCode, message: string) {
    super(message)
    this.name = 'GroupsApiError'
    this.code = code
  }
}

const flattenDetail = (value: unknown): string => {
  if (typeof value === 'string') {
    return value
  }

  if (Array.isArray(value)) {
    return value.map(flattenDetail).join(' ')
  }

  if (value && typeof value === 'object') {
    return Object.values(value as Record<string, unknown>).map(flattenDetail).join(' ')
  }

  return ''
}

const resolveGroupsError = (error: unknown): GroupsErrorCode => {
  if (!axios.isAxiosError(error)) {
    return 'UNKNOWN'
  }

  if (!error.response) {
    return 'NETWORK_ERROR'
  }

  const status = error.response.status
  const detail = flattenDetail((error.response.data as ErrorPayload | undefined)?.detail ?? error.response.data).toUpperCase()

  if (detail.includes('GROUP_NOT_FOUND')) {
    return 'GROUP_NOT_FOUND'
  }

  if (detail.includes('GROUP_ACCESS_DENIED')) {
    return 'ACCESS_DENIED'
  }

  if (detail.includes('GROUP_MAINTAINER_REQUIRED')) {
    return 'MAINTAINER_REQUIRED'
  }

  if (detail.includes('GROUP_NAME_ALREADY_EXISTS')) {
    return 'GROUP_NAME_ALREADY_EXISTS'
  }

  if (detail.includes('GROUP_USER_NOT_FOUND')) {
    return 'GROUP_USER_NOT_FOUND'
  }

  if (detail.includes('GROUP_CANNOT_CHANGE_MAINTAINER_ROLE')) {
    return 'CANNOT_CHANGE_MAINTAINER_ROLE'
  }

  if (status === 401) {
    return 'UNAUTHORIZED'
  }

  if (status === 422) {
    return 'VALIDATION_ERROR'
  }

  if (status >= 500) {
    return 'NETWORK_ERROR'
  }

  return 'UNKNOWN'
}

const toGroupsApiError = (error: unknown, message: string): GroupsApiError => {
  return new GroupsApiError(resolveGroupsError(error), message)
}

const authHeaders = (accessToken: string) => ({
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
})

export const getGroupList = async (accessToken: string): Promise<GroupListItem[]> => {
  try {
    const { data } = await httpClient.get<GroupListItem[]>('/groups/', authHeaders(accessToken))
    return data
  } catch (error) {
    throw toGroupsApiError(error, 'Не удалось загрузить список групп')
  }
}

export const createGroup = async (
  accessToken: string,
  payload: GroupCreatePayload,
): Promise<GroupListItem> => {
  try {
    const { data } = await httpClient.post<GroupListItem>('/groups/', payload, authHeaders(accessToken))
    return data
  } catch (error) {
    throw toGroupsApiError(error, 'Не удалось создать группу')
  }
}

export const updateGroupInfo = async (
  accessToken: string,
  groupId: string,
  payload: GroupUpdatePayload,
): Promise<GroupListItem> => {
  try {
    const { data } = await httpClient.patch<GroupListItem>(
      `/groups/${groupId}`,
      payload,
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toGroupsApiError(error, 'Не удалось обновить данные группы')
  }
}

export const deleteGroup = async (
  accessToken: string,
  groupId: string,
): Promise<GroupDeleteResponse> => {
  try {
    const { data } = await httpClient.delete<GroupDeleteResponse>(
      `/groups/${groupId}`,
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toGroupsApiError(error, 'Не удалось удалить группу')
  }
}

export const getGroupUsers = async (
  accessToken: string,
  groupId: string,
): Promise<GroupUserItem[]> => {
  try {
    const { data } = await httpClient.get<GroupUserItem[]>(
      `/groups/${groupId}/users`,
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toGroupsApiError(error, 'Не удалось загрузить участников группы')
  }
}

export const changeGroupUserRole = async (
  accessToken: string,
  groupId: string,
  targetUserId: string,
  role: GroupMutableRole,
): Promise<GroupUserItem> => {
  try {
    const { data } = await httpClient.patch<GroupUserItem>(
      `/groups/${groupId}/users/${targetUserId}/role`,
      { role },
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toGroupsApiError(error, 'Не удалось изменить роль участника')
  }
}

export const getGroupPlaylists = async (
  accessToken: string,
  groupId: string,
): Promise<GroupPlaylistItem[]> => {
  try {
    const { data } = await httpClient.get<GroupPlaylistItem[]>(
      `/groups/${groupId}/playlists`,
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toGroupsApiError(error, 'Не удалось загрузить плейлисты группы')
  }
}

export const getGroupQr = async (
  accessToken: string,
  groupId: string,
): Promise<GroupQrResponse> => {
  try {
    const { data } = await httpClient.get<GroupQrResponse>(
      `/groups/${groupId}/qr`,
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toGroupsApiError(error, 'Не удалось загрузить QR-код группы')
  }
}
