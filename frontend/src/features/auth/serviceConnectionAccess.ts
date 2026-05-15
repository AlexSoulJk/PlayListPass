const SERVICE_CONNECTION_PENDING_KEY = 'playlistpass.onboarding.service_connection.pending'

const PENDING_VALUE = 'pending'

export const markServiceConnectionPending = (): void => {
  window.localStorage.setItem(SERVICE_CONNECTION_PENDING_KEY, PENDING_VALUE)
}

export const consumeServiceConnectionPending = (): boolean => {
  const current = window.localStorage.getItem(SERVICE_CONNECTION_PENDING_KEY)
  if (current !== PENDING_VALUE) {
    return false
  }

  window.localStorage.removeItem(SERVICE_CONNECTION_PENDING_KEY)
  return true
}

export const clearServiceConnectionPending = (): void => {
  window.localStorage.removeItem(SERVICE_CONNECTION_PENDING_KEY)
}

