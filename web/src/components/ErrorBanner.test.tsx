import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ErrorBanner } from './ErrorBanner'

describe('ErrorBanner', () => {
  it('renders the message', () => {
    render(<ErrorBanner message="Something broke" />)
    expect(screen.getByText('Something broke')).toBeInTheDocument()
  })
})
