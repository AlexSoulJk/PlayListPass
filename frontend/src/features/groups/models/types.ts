export type GroupRole = 'MAINTAINER' | 'GUEST' | 'VIEWER'
export type GroupMutableRole = 'GUEST' | 'VIEWER'

export type GroupListItem = {
  id: string
  name: string
  image_url: string | null
  is_public: boolean
}

export type GroupCreatePayload = {
  name: string
  is_public: boolean
}

export type GroupUpdatePayload = {
  name?: string
  image_url?: string | null
}

export type GroupPlaylistItem = {
  id: string
  name: string
  image_url: string | null
  track_count: number
}

export type GroupQrResponse = {
  group_id: string
  qr_url: string
  expired_at: string
  is_expired: boolean
}

export type GroupUserItem = {
  id: string
  email: string
  name: string
  role: GroupRole
}

export type GroupDeleteResponse = {
  status: 'deleted'
  group_id: string
}

export type GroupsErrorCode =
  | 'UNAUTHORIZED'
  | 'GROUP_NOT_FOUND'
  | 'ACCESS_DENIED'
  | 'MAINTAINER_REQUIRED'
  | 'GROUP_NAME_ALREADY_EXISTS'
  | 'GROUP_USER_NOT_FOUND'
  | 'CANNOT_CHANGE_MAINTAINER_ROLE'
  | 'VALIDATION_ERROR'
  | 'NETWORK_ERROR'
  | 'UNKNOWN'
