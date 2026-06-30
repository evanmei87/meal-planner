import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatTile, MacroBar } from '@/features/meals/MacroDisplay'

describe('StatTile', () => {
  it('renders a label and value', () => {
    render(<StatTile label="Calories" value="650" />)
    expect(screen.getByText('Calories')).toBeInTheDocument()
    expect(screen.getByText('650')).toBeInTheDocument()
  })
})

describe('MacroBar', () => {
  it('renders three labelled segments sized by gram proportion', () => {
    render(<MacroBar protein={50} carbs={30} fat={20} />)
    const bar = screen.getByRole('img', { name: /protein 50g.*carbs 30g.*fat 20g/i })
    expect(bar).toBeInTheDocument()
    const protein = screen.getByTestId('macro-segment-protein')
    expect(protein).toHaveStyle({ width: '50%' })
  })

  it('renders nothing meaningful when all macros are zero', () => {
    render(<MacroBar protein={0} carbs={0} fat={0} />)
    expect(screen.getByTestId('macro-segment-protein')).toHaveStyle({ width: '0%' })
  })
})
