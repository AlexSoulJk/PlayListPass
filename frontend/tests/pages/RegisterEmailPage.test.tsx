import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { AuthContext } from '../../src/app/providers/authContext'
import { RegisterEmailPage } from '../../src/features/auth/ui/pages/RegisterEmailPage/RegisterEmailPage'
import { createAuthContextValue } from '../utils/createAuthContextValue'

describe('RegisterEmailPage', () => {
  it('renders user-exists backend error in email field', () => {
    render(
      <MemoryRouter initialEntries={['/auth/register/email?error=user-exists']}>
        <AuthContext.Provider value={createAuthContextValue()}>
          <Routes>
            <Route path="/auth/register/email" element={<RegisterEmailPage />} />
          </Routes>
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(screen.getByText('Пользователь уже зарегистрирован')).toBeInTheDocument()
  })
})
