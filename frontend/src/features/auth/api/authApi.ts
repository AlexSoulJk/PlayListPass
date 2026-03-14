import axios from 'axios'
import { httpClient } from '../../../shared/api/httpClient'
import type { AuthErrorCode, AuthSession, LoginPayload, RegisterPayload } from '../types'

type LoginResponse = {
  access_token: string
  token_type: string
}

export class AuthApiError extends Error {
  code: AuthErrorCode

  constructor(code: AuthErrorCode, message: string) {
    super(message)
    this.name = 'AuthApiError'
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

const resolveAuthError = (error: unknown, fallback: AuthErrorCode): AuthErrorCode => {
  if (!axios.isAxiosError(error)) {
    return fallback
  }

  if (!error.response) {
    return 'NETWORK_ERROR'
  }

  const status = error.response.status
  const detail = flattenDetail(error.response.data).toUpperCase()

  if (detail.includes('REGISTER_USER_ALREADY_EXISTS')) {
    return 'USER_ALREADY_EXISTS'
  }

  if (detail.includes('LOGIN_BAD_CREDENTIALS')) {
    return 'INVALID_CREDENTIALS'
  }

  if (status === 401) {
    return 'INVALID_CREDENTIALS'
  }

  if (status === 400 && fallback === 'INVALID_CREDENTIALS') {
    return 'INVALID_CREDENTIALS'
  }

  if (status >= 500) {
    return 'NETWORK_ERROR'
  }

  return fallback
}

const toAuthApiError = (error: unknown, fallback: AuthErrorCode, message: string): AuthApiError => {
  return new AuthApiError(resolveAuthError(error, fallback), message)
}

export const login = async ({ email, password }: LoginPayload): Promise<AuthSession> => {
  const payload = new URLSearchParams()
  payload.set('username', email)
  payload.set('password', password)
  payload.set('grant_type', 'password')
  payload.set('scope', '')
  payload.set('client_id', '')
  payload.set('client_secret', '')

  try {
    const { data } = await httpClient.post<LoginResponse>('/auth/jwt/login', payload, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    return {
      accessToken: data.access_token,
      tokenType: 'bearer',
      email,
    }
  } catch (error) {
    throw toAuthApiError(error, 'INVALID_CREDENTIALS', 'Не удалось выполнить вход')
  }
}

export const register = async ({ email, password, name }: RegisterPayload): Promise<void> => {
  try {
    await httpClient.post('/auth/register', {
      email,
      password,
      name,
    })
  } catch (error) {
    throw toAuthApiError(error, 'UNKNOWN', 'Не удалось зарегистрировать пользователя')
  }
}
