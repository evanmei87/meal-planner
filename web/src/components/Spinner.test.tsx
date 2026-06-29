import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Spinner } from './Spinner'

describe('Spinner', () => {
  it('renders a spinning indicator', () => {
    const { container } = render(<Spinner />)
    expect(container.querySelector('.animate-spin')).not.toBeNull()
  })
})
