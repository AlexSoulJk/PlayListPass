import axios from 'axios'
import { httpClient } from '../../../shared/api/httpClient'
import type {
  GroupPlaylistItem,
  PlaylistCreatePayload,
  PlaylistImageUploadInitPayload,
  PlaylistImageUploadInitResponse,
  PlaylistPlaybackQueue,
  PlaylistPlaybackTrackItem,
  PlaylistTrackDeleteResponse,
  PlaylistTrackItem,
  PlaylistUpdatePayload,
} from '../models/types'

type ErrorPayload = {
  detail?: unknown
}

type PlaylistErrorCode =
  | 'UNAUTHORIZED'
  | 'GROUP_NOT_FOUND'
  | 'PLAYLIST_NOT_FOUND'
  | 'ACCESS_DENIED'
  | 'PLAYLIST_NAME_ALREADY_EXISTS'
  | 'PLAYLIST_IMAGE_UNSUPPORTED_FORMAT'
  | 'PLAYLIST_IMAGE_OBJECT_NOT_FOUND'
  | 'PLAYLIST_IMAGE_UPLOAD_FAILED'
  | 'PLAYLIST_TRACK_NOT_FOUND'
  | 'PLAYLIST_AUDIO_NOT_AVAILABLE'
  | 'GROUP_TRACK_EDIT_FORBIDDEN'
  | 'STORAGE_BACKEND_NOT_AVAILABLE'
  | 'VALIDATION_ERROR'
  | 'NETWORK_ERROR'
  | 'UNKNOWN'

type PlaylistResponse = {
  id: string
  name: string
  image_url: string | null
}

type PlaylistDeleteResponse = {
  status: 'deleted'
  playlist_id: string
}

type PlaylistTracksResponse = {
  playlist_id: string
  items: PlaylistTrackItem[]
}

type PlaylistPlaybackTrackResponse = PlaylistPlaybackTrackItem
type PlaylistPlaybackQueueResponse = PlaylistPlaybackQueue

export class PlaylistsApiError extends Error {
  code: PlaylistErrorCode

  constructor(code: PlaylistErrorCode, message: string) {
    super(message)
    this.name = 'PlaylistsApiError'
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

const resolvePlaylistError = (error: unknown): PlaylistErrorCode => {
  if (!axios.isAxiosError(error)) {
    return 'UNKNOWN'
  }

  if (!error.response) {
    return 'NETWORK_ERROR'
  }

  const status = error.response.status
  const detail = flattenDetail((error.response.data as ErrorPayload | undefined)?.detail ?? error.response.data).toUpperCase()

  if (detail.includes('PLAYLIST_NAME_ALREADY_EXISTS')) {
    return 'PLAYLIST_NAME_ALREADY_EXISTS'
  }

  if (detail.includes('GROUP_NOT_FOUND')) {
    return 'GROUP_NOT_FOUND'
  }

  if (detail.includes('PLAYLIST_NOT_FOUND')) {
    return 'PLAYLIST_NOT_FOUND'
  }

  if (detail.includes('GROUP_ACCESS_DENIED') || detail.includes('GROUP_MAINTAINER_REQUIRED')) {
    return 'ACCESS_DENIED'
  }

  if (detail.includes('PLAYLIST_IMAGE_UNSUPPORTED_FORMAT') || detail.includes('PLAYLIST_IMAGE_FORMAT_MISMATCH')) {
    return 'PLAYLIST_IMAGE_UNSUPPORTED_FORMAT'
  }

  if (detail.includes('PLAYLIST_IMAGE_OBJECT_NOT_FOUND')) {
    return 'PLAYLIST_IMAGE_OBJECT_NOT_FOUND'
  }

  if (detail.includes('PLAYLIST_TRACK_NOT_FOUND')) {
    return 'PLAYLIST_TRACK_NOT_FOUND'
  }

  if (detail.includes('PLAYLIST_AUDIO_NOT_AVAILABLE')) {
    return 'PLAYLIST_AUDIO_NOT_AVAILABLE'
  }

  if (detail.includes('GROUP_TRACK_EDIT_FORBIDDEN')) {
    return 'GROUP_TRACK_EDIT_FORBIDDEN'
  }

  if (detail.includes('STORAGE_BACKEND_NOT_AVAILABLE')) {
    return 'STORAGE_BACKEND_NOT_AVAILABLE'
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

const toPlaylistsApiError = (error: unknown, message: string): PlaylistsApiError => {
  return new PlaylistsApiError(resolvePlaylistError(error), message)
}

const authHeaders = (accessToken: string) => ({
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
})

const toGroupPlaylistItem = (payload: PlaylistResponse, trackCount = 0): GroupPlaylistItem => {
  return {
    id: payload.id,
    name: payload.name,
    image_url: payload.image_url,
    track_count: trackCount,
  }
}

export const createPlaylist = async (
  accessToken: string,
  groupId: string,
  payload: PlaylistCreatePayload,
): Promise<GroupPlaylistItem> => {
  try {
    const { data } = await httpClient.post<PlaylistResponse>(
      `/playlist/${groupId}/create`,
      payload,
      authHeaders(accessToken),
    )
    return toGroupPlaylistItem(data)
  } catch (error) {
    throw toPlaylistsApiError(error, 'Failed to create playlist')
  }
}

export const updatePlaylist = async (
  accessToken: string,
  groupId: string,
  playlistId: string,
  payload: PlaylistUpdatePayload,
): Promise<GroupPlaylistItem> => {
  try {
    const { data } = await httpClient.patch<PlaylistResponse>(
      `/playlist/${groupId}/${playlistId}`,
      payload,
      authHeaders(accessToken),
    )
    return toGroupPlaylistItem(data)
  } catch (error) {
    throw toPlaylistsApiError(error, 'Failed to update playlist')
  }
}

export const uploadPlaylistImage = async (
  accessToken: string,
  groupId: string,
  playlistId: string,
  file: File,
): Promise<GroupPlaylistItem> => {
  const initPayload: PlaylistImageUploadInitPayload = {
    filename: file.name,
    content_type: file.type || null,
  }

  let initResponse: PlaylistImageUploadInitResponse
  try {
    const { data } = await httpClient.post<PlaylistImageUploadInitResponse>(
      `/playlist/${groupId}/${playlistId}/image/upload-init`,
      initPayload,
      authHeaders(accessToken),
    )
    initResponse = data
  } catch (error) {
    throw toPlaylistsApiError(error, 'Failed to initialize playlist image upload')
  }

  try {
    await axios.put(initResponse.upload_url, file, {
      headers: {
        'Content-Type': file.type || 'application/octet-stream',
      },
    })
  } catch {
    throw new PlaylistsApiError('PLAYLIST_IMAGE_UPLOAD_FAILED', 'Failed to upload image file to storage')
  }

  try {
    const { data } = await httpClient.post<PlaylistResponse>(
      `/playlist/${groupId}/${playlistId}/image/commit`,
      {
        object_key: initResponse.object_key,
      },
      authHeaders(accessToken),
    )
    return toGroupPlaylistItem(data)
  } catch (error) {
    throw toPlaylistsApiError(error, 'Failed to commit playlist image upload')
  }
}

export const deletePlaylist = async (
  accessToken: string,
  groupId: string,
  playlistId: string,
): Promise<PlaylistDeleteResponse> => {
  try {
    const { data } = await httpClient.delete<PlaylistDeleteResponse>(
      `/playlist/${groupId}/${playlistId}`,
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toPlaylistsApiError(error, 'Failed to delete playlist')
  }
}

export const getPlaylistTracks = async (
  accessToken: string,
  groupId: string,
  playlistId: string,
): Promise<PlaylistTrackItem[]> => {
  try {
    const { data } = await httpClient.get<PlaylistTracksResponse>(
      `/playlist/${groupId}/${playlistId}/tracks`,
      authHeaders(accessToken),
    )
    return data.items
  } catch (error) {
    throw toPlaylistsApiError(error, 'Failed to load playlist tracks')
  }
}

export const removeTrackFromPlaylist = async (
  accessToken: string,
  groupId: string,
  playlistId: string,
  trackId: number,
): Promise<PlaylistTrackDeleteResponse> => {
  try {
    const { data } = await httpClient.delete<PlaylistTrackDeleteResponse>(
      `/playlist/${groupId}/${playlistId}/tracks/${trackId}`,
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toPlaylistsApiError(error, 'Failed to remove track from playlist')
  }
}

export const getPlaylistFirstPlayableTrack = async (
  accessToken: string,
  groupId: string,
  playlistId: string,
): Promise<PlaylistPlaybackTrackItem> => {
  try {
    const { data } = await httpClient.get<PlaylistPlaybackTrackResponse>(
      `/playlist/${groupId}/${playlistId}/tracks/playback/first`,
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toPlaylistsApiError(error, 'Failed to load playable track')
  }
}

export const getPlaylistPlaybackQueue = async (
  accessToken: string,
  groupId: string,
  playlistId: string,
): Promise<PlaylistPlaybackQueue> => {
  try {
    const { data } = await httpClient.get<PlaylistPlaybackQueueResponse>(
      `/playlist/${groupId}/${playlistId}/tracks/playback`,
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toPlaylistsApiError(error, 'Failed to load playback queue')
  }
}
