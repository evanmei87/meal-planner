import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PulsatingButton } from './PulsatingButton'

function mockPrefersReducedMotion(matches: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })) as unknown as typeof window.matchMedia
}

describe('PulsatingButton', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders its children when not pulsating', () => {
    mockPrefersReducedMotion(false)
    render(
      <PulsatingButton>
        <button>Generate Plan</button>
      </PulsatingButton>
    )
    expect(screen.getByRole('button', { name: 'Generate Plan' })).toBeInTheDocument()
  })

  it('renders its children while pulsating', () => {
    mockPrefersReducedMotion(false)
    render(
      <PulsatingButton pulsating>
        <button>Generating…</button>
      </PulsatingButton>
    )
    expect(screen.getByRole('button', { name: 'Generating…' })).toBeInTheDocument()
  })

  it('renders its children without pulsing when the user prefers reduced motion', () => {
    mockPrefersReducedMotion(true)
    render(
      <PulsatingButton pulsating>
        <button>Generating…</button>
      </PulsatingButton>
    )
    expect(screen.getByRole('button', { name: 'Generating…' })).toBeInTheDocument()
  })
})
