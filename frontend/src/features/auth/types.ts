export type AuthErrorCode =
  | 'INVALID_CREDENTIALS'
  | 'USER_ALREADY_EXISTS'
  | 'NETWORK_ERROR'
  | 'UNKNOWN'

export type AuthStatus = 'anonymous' | 'authenticated' | 'loading'

export interface AuthSession {
  accessToken: string
  tokenType: 'bearer'
  email: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  password: string
  name: string
}

export interface RegisterStepState {
  email: string
  name: string
  password: string
  confirmPassword: string
}
