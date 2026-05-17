import type { GroupRole, GroupPlaylistItem } from '../../groups/models/types'

export type StreamingService = 'YANDEX_MUSIC' | 'YOUTUBE' | 'SPOTIFY'

export type SearchTrackItem = {
  service: StreamingService
  service_track_id: string
  internal_track_id: number | null
  is_in_db: boolean
  title: string
  artist: string
  cover_url: string | null
  external_url: string | null
  duration_sec: number | null
}

export type SearchPagination = {
  page: number
  page_size: number
  total: number
  pages: number
}

export type SearchTracksPayload = {
  group_id: string
  query: string
  services: StreamingService[]
  page: number
  page_size: number
}

export type SearchTracksResponse = {
  items: SearchTrackItem[]
  pagination: SearchPagination
  service_availability: Record<StreamingService, boolean>
}

export type AddTrackToPlaylistPayload = {
  internal_track_id?: number
  service?: StreamingService
  service_track_id?: string
  title?: string
  artist?: string
  cover_url?: string | null
  external_url?: string | null
  duration_sec?: number | null
  imported_from_search?: boolean
}

export type AddTrackToPlaylistResponse = {
  status: 'added'
  playlist_id: string
  track_id: number
  created_new_track: boolean
}

export type SearchRouteState = {
  groupId?: string
  groupName?: string | null
  groupImageUrl?: string | null
  playlistId?: string
  playlistName?: string | null
  groupRole?: GroupRole | null
  playlists?: GroupPlaylistItem[]
}

export type SearchErrorCode =
  | 'UNAUTHORIZED'
  | 'GROUP_NOT_FOUND'
  | 'PLAYLIST_NOT_FOUND'
  | 'TRACK_NOT_FOUND'
  | 'PLAYLIST_TRACK_ALREADY_EXISTS'
  | 'GROUP_TRACK_EDIT_FORBIDDEN'
  | 'TRACK_SOURCE_REQUIRED'
  | 'TRACK_METADATA_REQUIRED'
  | 'TRACK_EXTERNAL_URL_REQUIRED'
  | 'VALIDATION_ERROR'
  | 'NETWORK_ERROR'
  | 'UNKNOWN'
