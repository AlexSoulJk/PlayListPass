import { useEffect, useReducer, type PropsWithChildren } from 'react'
import { AuthApiError, login, register } from '../../features/auth/api/authApi'
import { clearStoredSession, loadStoredSession, saveStoredSession } from '../../features/auth/authStorage'
import type {
  AuthSession,
  AuthStatus,
  LoginPayload,
  RegisterPayload,
  RegisterStepState,
} from '../../features/auth/types'
import { AuthContext } from './authContext'

type AuthState = {
  status: AuthStatus
  session: AuthSession | null
  registerDraft: RegisterStepState
}

type AuthAction =
  | { type: 'RESTORE_SESSION'; session: AuthSession | null }
  | { type: 'SET_ANONYMOUS' }
  | { type: 'SIGN_IN'; session: AuthSession }
  | { type: 'SIGN_OUT' }
  | { type: 'UPDATE_REGISTER_DRAFT'; patch: Partial<RegisterStepState> }
  | { type: 'RESET_REGISTER_DRAFT' }

const emptyRegisterDraft: RegisterStepState = {
  email: '',
  name: '',
  password: '',
  confirmPassword: '',
}

const initialState: AuthState = {
  status: 'loading',
  session: null,
  registerDraft: emptyRegisterDraft,
}

const reducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'RESTORE_SESSION':
      return {
        ...state,
        status: action.session ? 'authenticated' : 'anonymous',
        session: action.session,
      }
    case 'SET_ANONYMOUS':
      return {
        ...state,
        status: 'anonymous',
        session: null,
      }
    case 'SIGN_IN':
      return {
        status: 'authenticated',
        session: action.session,
        registerDraft: emptyRegisterDraft,
      }
    case 'SIGN_OUT':
      return {
        status: 'anonymous',
        session: null,
        registerDraft: emptyRegisterDraft,
      }
    case 'UPDATE_REGISTER_DRAFT':
      return {
        ...state,
        registerDraft: {
          ...state.registerDraft,
          ...action.patch,
        },
      }
    case 'RESET_REGISTER_DRAFT':
      return {
        ...state,
        registerDraft: emptyRegisterDraft,
      }
    default:
      return state
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(reducer, initialState)

  useEffect(() => {
    const storedSession = loadStoredSession()
    dispatch({ type: 'RESTORE_SESSION', session: storedSession })
  }, [])

  const signIn = async (payload: LoginPayload) => {
    try {
      const session = await login(payload)
      saveStoredSession(session)
      dispatch({ type: 'SIGN_IN', session })
    } catch (error) {
      dispatch({ type: 'SET_ANONYMOUS' })
      throw error
    }
  }

  const registerOnly = async (payload: RegisterPayload) => {
    try {
      await register(payload)
    } catch (error) {
      if (error instanceof AuthApiError) {
        throw error
      }
      throw new AuthApiError('UNKNOWN', 'Failed to complete registration')
    }
  }

  const signOut = () => {
    clearStoredSession()
    dispatch({ type: 'SIGN_OUT' })
  }

  const setRegisterDraft = (patch: Partial<RegisterStepState>) => {
    dispatch({ type: 'UPDATE_REGISTER_DRAFT', patch })
  }

  const resetRegisterDraft = () => {
    dispatch({ type: 'RESET_REGISTER_DRAFT' })
  }

  return (
    <AuthContext.Provider
      value={{
        status: state.status,
        session: state.session,
        registerDraft: state.registerDraft,
        signIn,
        registerOnly,
        signOut,
        setRegisterDraft,
        resetRegisterDraft,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
