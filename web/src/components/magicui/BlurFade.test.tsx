import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { BlurFade } from './BlurFade'

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

describe('BlurFade', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders its children', () => {
    mockPrefersReducedMotion(false)
    render(
      <BlurFade transitionKey="monday">
        <p>Monday's plan</p>
      </BlurFade>
    )
    expect(screen.getByText("Monday's plan")).toBeInTheDocument()
  })

  it('still renders its children when the user prefers reduced motion', () => {
    mockPrefersReducedMotion(true)
    render(
      <BlurFade transitionKey="tuesday">
        <p>Tuesday's plan</p>
      </BlurFade>
    )
    expect(screen.getByText("Tuesday's plan")).toBeInTheDocument()
  })

  it('remounts and still shows the new content when the transition key changes', () => {
    mockPrefersReducedMotion(false)
    const { rerender } = render(
      <BlurFade transitionKey="monday">
        <p>Monday's plan</p>
      </BlurFade>
    )
    rerender(
      <BlurFade transitionKey="tuesday">
        <p>Tuesday's plan</p>
      </BlurFade>
    )
    expect(screen.queryByText("Monday's plan")).not.toBeInTheDocument()
    expect(screen.getByText("Tuesday's plan")).toBeInTheDocument()
  })
})
