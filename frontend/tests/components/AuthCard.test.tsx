import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AuthCard } from '../../src/features/auth/ui/components/AuthCard/AuthCard'

describe('AuthCard', () => {
  it('renders children content', () => {
    render(
      <AuthCard>
        <div>card-content</div>
      </AuthCard>,
    )

    expect(screen.getByText('card-content')).toBeInTheDocument()
  })
})
