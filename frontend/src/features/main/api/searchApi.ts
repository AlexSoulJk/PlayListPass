import axios from 'axios'
import { httpClient } from '../../../shared/api/httpClient'
import type {
  AddTrackToPlaylistPayload,
  AddTrackToPlaylistResponse,
  SearchErrorCode,
  SearchTracksPayload,
  SearchTracksResponse,
} from '../models/searchTypes'

type ErrorPayload = {
  detail?: unknown
}

export class SearchApiError extends Error {
  code: SearchErrorCode

  constructor(code: SearchErrorCode, message: string) {
    super(message)
    this.name = 'SearchApiError'
    this.code = code
  }
}

const authHeaders = (accessToken: string) => ({
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
})

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

const resolveSearchError = (error: unknown): SearchErrorCode => {
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
  if (detail.includes('PLAYLIST_NOT_FOUND')) {
    return 'PLAYLIST_NOT_FOUND'
  }
  if (detail.includes('TRACK_NOT_FOUND')) {
    return 'TRACK_NOT_FOUND'
  }
  if (detail.includes('PLAYLIST_TRACK_ALREADY_EXISTS')) {
    return 'PLAYLIST_TRACK_ALREADY_EXISTS'
  }
  if (detail.includes('GROUP_TRACK_EDIT_FORBIDDEN')) {
    return 'GROUP_TRACK_EDIT_FORBIDDEN'
  }
  if (detail.includes('TRACK_SOURCE_REQUIRED')) {
    return 'TRACK_SOURCE_REQUIRED'
  }
  if (detail.includes('TRACK_METADATA_REQUIRED')) {
    return 'TRACK_METADATA_REQUIRED'
  }
  if (detail.includes('TRACK_EXTERNAL_URL_REQUIRED')) {
    return 'TRACK_EXTERNAL_URL_REQUIRED'
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

const toSearchApiError = (error: unknown, message: string): SearchApiError => {
  return new SearchApiError(resolveSearchError(error), message)
}

export const searchTracks = async (
  accessToken: string,
  payload: SearchTracksPayload,
): Promise<SearchTracksResponse> => {
  try {
    const { data } = await httpClient.post<SearchTracksResponse>(
      '/search/tracks',
      payload,
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toSearchApiError(error, 'Не удалось выполнить поиск треков')
  }
}

export const addTrackToPlaylist = async (
  accessToken: string,
  groupId: string,
  playlistId: string,
  payload: AddTrackToPlaylistPayload,
): Promise<AddTrackToPlaylistResponse> => {
  try {
    const { data } = await httpClient.post<AddTrackToPlaylistResponse>(
      `/playlist/${groupId}/${playlistId}/tracks`,
      payload,
      authHeaders(accessToken),
    )
    return data
  } catch (error) {
    throw toSearchApiError(error, 'Не удалось добавить трек в плейлист')
  }
}
