import type { AuthSession } from './types'

const AUTH_SESSION_KEY = 'playlistpass.auth.session'

const isSessionShape = (value: unknown): value is AuthSession => {
  if (!value || typeof value !== 'object') {
    return false
  }

  const candidate = value as Record<string, unknown>

  return (
    typeof candidate.accessToken === 'string' &&
    typeof candidate.email === 'string' &&
    candidate.tokenType === 'bearer'
  )
}

export const loadStoredSession = (): AuthSession | null => {
  try {
    const raw = window.localStorage.getItem(AUTH_SESSION_KEY)
    if (!raw) {
      return null
    }

    const parsed: unknown = JSON.parse(raw)
    return isSessionShape(parsed) ? parsed : null
  } catch {
    return null
  }
}

export const saveStoredSession = (session: AuthSession): void => {
  window.localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(session))
}

export const clearStoredSession = (): void => {
  window.localStorage.removeItem(AUTH_SESSION_KEY)
}
