import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext } from '../../src/app/providers/authContext'
import { PlaybackProvider } from '../../src/app/providers/PlaybackProvider'
import { ThemeProvider } from '../../src/app/theme/ThemeProvider'
import { MainWorkspaceLayout } from '../../src/features/main/ui/layout/MainWorkspaceLayout/MainWorkspaceLayout'
import { createAuthContextValue } from '../utils/createAuthContextValue'

describe('MainWorkspaceLayout', () => {
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
        <ThemeProvider>
          <AuthContext.Provider value={authValue}>
            <PlaybackProvider>
              <Routes>
                <Route path="/app" element={<MainWorkspaceLayout />}>
                  <Route index element={<div>workspace-route</div>} />
                </Route>
                <Route path="/" element={<div>landing-route</div>} />
              </Routes>
            </PlaybackProvider>
          </AuthContext.Provider>
        </ThemeProvider>
      </MemoryRouter>,
    )

    expect(screen.getByText(/demo@example.com/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Выйти' }))

    expect(signOut).toHaveBeenCalledTimes(1)
    expect(screen.getByText('landing-route')).toBeInTheDocument()
  })
})
