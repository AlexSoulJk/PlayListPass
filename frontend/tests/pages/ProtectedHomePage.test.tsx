import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '../../src/app/providers/authContext'
import { ProtectedHomePage } from '../../src/features/auth/ui/pages/ProtectedHomePage/ProtectedHomePage'
import { createAuthContextValue } from '../utils/createAuthContextValue'

describe('ProtectedHomePage', () => {
  it('renders current session email and logs out to landing', async () => {
    const user = userEvent.setup()
    const signOut = vi.fn()
    const authValue = createAuthContextValue({
      status: 'authenticated',
      session: {
        accessToken: 'token',
        tokenType: 'bearer',
        email: 'demo@example.com',
      },
      signOut,
    })

    render(
      <MemoryRouter initialEntries={['/app']}>
        <AuthContext.Provider value={authValue}>
          <Routes>
            <Route path="/app" element={<ProtectedHomePage />} />
            <Route path="/" element={<div>landing-route</div>} />
          </Routes>
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(screen.getByText(/demo@example.com/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Выйти' }))

    expect(signOut).toHaveBeenCalledTimes(1)
    expect(screen.getByText('landing-route')).toBeInTheDocument()
  })
})
