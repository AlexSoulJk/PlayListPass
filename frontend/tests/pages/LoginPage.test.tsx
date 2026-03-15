import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '../../src/app/providers/authContext'
import { AuthApiError } from '../../src/features/auth/api/authApi'
import { LoginPage } from '../../src/features/auth/ui/pages/LoginPage/LoginPage'
import { createAuthContextValue } from '../utils/createAuthContextValue'

describe('LoginPage', () => {
  it('shows invalid credentials in password field only', async () => {
    const user = userEvent.setup()
    const signIn = vi.fn().mockRejectedValue(new AuthApiError('INVALID_CREDENTIALS', 'bad credentials'))

    const authValue = createAuthContextValue({ signIn })

    render(
      <MemoryRouter>
        <AuthContext.Provider value={authValue}>
          <LoginPage />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText('Почта'), 'demo@example.com')
    await user.type(screen.getByLabelText('Пароль'), 'Passw0rd123!')
    await user.click(screen.getByRole('button', { name: 'Войти' }))

    await waitFor(() => {
      expect(screen.getByText('Неверные почта или пароль')).toBeInTheDocument()
    })

    expect(screen.getAllByText('Неверные почта или пароль')).toHaveLength(1)
    expect(signIn).toHaveBeenCalledTimes(1)
  })
})
