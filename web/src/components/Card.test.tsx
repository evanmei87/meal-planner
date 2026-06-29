import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Card } from './Card'

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Hello</Card>)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('applies an extra className', () => {
    render(<Card className="custom-class">Body</Card>)
    expect(screen.getByText('Body')).toHaveClass('custom-class')
  })
})
