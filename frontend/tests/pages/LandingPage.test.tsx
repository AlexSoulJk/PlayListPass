import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { LandingPage } from '../../src/features/auth/ui/pages/LandingPage/LandingPage'

describe('LandingPage', () => {
  it('navigates to login and register routes from CTA buttons', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth/login" element={<div>login-route</div>} />
          <Route path="/auth/register/email" element={<div>register-route</div>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText('Собирайте общий плейлист за секунды')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Войти' }))
    expect(screen.getByText('login-route')).toBeInTheDocument()
  })

  it('opens register route from register button', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth/register/email" element={<div>register-route</div>} />
        </Routes>
      </MemoryRouter>,
    )

    await user.click(screen.getByRole('button', { name: 'Регистрация' }))
    expect(screen.getByText('register-route')).toBeInTheDocument()
  })
})
