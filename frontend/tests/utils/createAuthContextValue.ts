import type { AuthContextValue } from '../../src/app/providers/authContext'

export const createAuthContextValue = (overrides: Partial<AuthContextValue> = {}): AuthContextValue => ({
  status: 'anonymous',
  session: null,
  registerDraft: {
    email: '',
    name: '',
    password: '',
    confirmPassword: '',
  },
  signIn: async () => {},
  registerOnly: async () => {},
  signOut: () => {},
  setRegisterDraft: () => {},
  resetRegisterDraft: () => {},
  ...overrides,
})
