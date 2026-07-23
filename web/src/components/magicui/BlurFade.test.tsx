import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { BlurFade } from './BlurFade'

describe('BlurFade', () => {
  it('renders its children with the reveal animation classes, respecting reduced motion', () => {
    render(
      <BlurFade transitionKey="monday">
        <p>Monday's plan</p>
      </BlurFade>
    )
    const wrapper = screen.getByText("Monday's plan").parentElement
    expect(wrapper).toHaveClass('animate-in', 'fade-in', 'slide-in-from-bottom-2')
    expect(wrapper).toHaveClass('motion-reduce:animate-none')
  })

  it('remounts and still shows the new content when the transition key changes', () => {
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
