import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AuthContext } from '../../src/app/providers/authContext'
import { AppRouter } from '../../src/app/router/AppRouter'
import { createAuthContextValue } from '../utils/createAuthContextValue'

describe('AppRouter', () => {
  it('redirects anonymous user from /app to /auth/login', () => {
    const authValue = createAuthContextValue({ status: 'anonymous' })

    render(
      <MemoryRouter initialEntries={['/app']}>
        <AuthContext.Provider value={authValue}>
          <AppRouter />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(screen.getByLabelText('Почта')).toBeInTheDocument()
    expect(screen.getByLabelText('Пароль')).toBeInTheDocument()
  })

  it('redirects authenticated user from /auth/login to /app', () => {
    const authValue = createAuthContextValue({
      status: 'authenticated',
      session: {
        accessToken: 'token',
        tokenType: 'bearer',
        email: 'demo@example.com',
      },
    })

    render(
      <MemoryRouter initialEntries={['/auth/login']}>
        <AuthContext.Provider value={authValue}>
          <AppRouter />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(screen.getByText(/demo@example.com/i)).toBeInTheDocument()
  })
})
