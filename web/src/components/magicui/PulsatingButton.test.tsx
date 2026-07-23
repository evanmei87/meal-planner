import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { PulsatingButton } from './PulsatingButton'

describe('PulsatingButton', () => {
  it('renders its children when not pulsating', () => {
    render(
      <PulsatingButton>
        <button>Generate Plan</button>
      </PulsatingButton>
    )
    expect(screen.getByRole('button', { name: 'Generate Plan' })).toBeInTheDocument()
  })

  it('omits the pulsing ring when not pulsating', () => {
    render(
      <PulsatingButton>
        <button>Generate Plan</button>
      </PulsatingButton>
    )
    expect(document.querySelector('[aria-hidden="true"]')).not.toBeInTheDocument()
  })

  it('renders a pulsing ring that respects reduced motion while pulsating', () => {
    render(
      <PulsatingButton pulsating>
        <button>Generating…</button>
      </PulsatingButton>
    )
    expect(screen.getByRole('button', { name: 'Generating…' })).toBeInTheDocument()
    const ring = document.querySelector('[aria-hidden="true"]')
    expect(ring).toBeInTheDocument()
    expect(ring).toHaveClass('animate-ping')
    expect(ring).toHaveClass('motion-reduce:animate-none')
  })
})
