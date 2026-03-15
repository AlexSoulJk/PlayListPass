import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { AuthInput } from '../../src/features/auth/ui/components/AuthInput/AuthInput'

describe('AuthInput', () => {
  it('renders error message under input and marks input invalid', () => {
    render(<AuthInput errorMessage="Неверный формат почты" id="email" label="Почта" type="email" />)

    const input = screen.getByLabelText('Почта')

    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByText('Неверный формат почты')).toBeInTheDocument()
  })

  it('toggles password visibility', async () => {
    const user = userEvent.setup()

    render(<AuthInput id="password" label="Пароль" type="password" />)

    const input = screen.getByLabelText('Пароль')
    const toggle = screen.getByRole('button', { name: 'Показать пароль' })

    expect(input).toHaveAttribute('type', 'password')

    await user.click(toggle)
    expect(input).toHaveAttribute('type', 'text')

    await user.click(screen.getByRole('button', { name: 'Скрыть пароль' }))
    expect(input).toHaveAttribute('type', 'password')
  })
})
