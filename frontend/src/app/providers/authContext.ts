import { createContext } from 'react'
import type {
  AuthSession,
  AuthStatus,
  LoginPayload,
  RegisterPayload,
  RegisterStepState,
} from '../../features/auth/types'

export type AuthContextValue = {
  status: AuthStatus
  session: AuthSession | null
  registerDraft: RegisterStepState
  signIn: (payload: LoginPayload) => Promise<void>
  registerOnly: (payload: RegisterPayload) => Promise<void>
  signOut: () => void
  setRegisterDraft: (patch: Partial<RegisterStepState>) => void
  resetRegisterDraft: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
