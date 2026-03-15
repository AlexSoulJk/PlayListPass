import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AuthContext } from '../../src/app/providers/authContext'
import { RegisterPasswordPage } from '../../src/features/auth/ui/pages/RegisterPasswordPage/RegisterPasswordPage'
import { createAuthContextValue } from '../utils/createAuthContextValue'

describe('RegisterPasswordPage', () => {
  it('redirects to email step when draft email is empty', () => {
    render(
      <MemoryRouter initialEntries={['/auth/register/password']}>
        <AuthContext.Provider value={createAuthContextValue()}>
          <Routes>
            <Route path="/auth/register/password" element={<RegisterPasswordPage />} />
            <Route path="/auth/register/email" element={<div>email-step-route</div>} />
          </Routes>
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(screen.getByText('email-step-route')).toBeInTheDocument()
  })

  it('renders register credentials form when draft email exists', () => {
    const authValue = createAuthContextValue({
      registerDraft: {
        email: 'demo@example.com',
        name: '',
        password: '',
        confirmPassword: '',
      },
    })

    render(
      <MemoryRouter initialEntries={['/auth/register/password']}>
        <AuthContext.Provider value={authValue}>
          <Routes>
            <Route path="/auth/register/password" element={<RegisterPasswordPage />} />
          </Routes>
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(screen.getByLabelText('Имя')).toBeInTheDocument()
    expect(screen.getByLabelText('Пароль')).toBeInTheDocument()
  })
})
