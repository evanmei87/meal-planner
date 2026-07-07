import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MealDetail } from '@/features/meals/MealDetail'
import type { MealResponse } from '@/api/types'

const MEAL: MealResponse = {
  name: 'Chicken Bowl',
  version: '2024-01-01',
  category: 'Dinner',
  servings: 2,
  macros: { calories: 650, protein: 45, carbs: 55, fat: 8 },
  ingredients: ['Chicken', 'Rice'],
  instructions: ['Season chicken', 'Sear chicken', 'Serve over rice'],
  tags: ['high_protein'],
}

describe('MealDetail', () => {
  it('renders name, servings, macros, ingredients, and numbered steps', () => {
    render(<MealDetail meal={MEAL} />)
    expect(screen.getByText('Chicken Bowl')).toBeInTheDocument()
    expect(screen.getByText(/makes 2 servings/i)).toBeInTheDocument()
    expect(screen.getByText('650')).toBeInTheDocument()
    expect(screen.getByText('Season chicken')).toBeInTheDocument()
    expect(screen.getByText('Chicken')).toBeInTheDocument()
    expect(screen.getByText('high_protein')).toBeInTheDocument()
  })

  it('uses singular "serving" when servings is 1', () => {
    render(<MealDetail meal={{ ...MEAL, servings: 1 }} />)
    expect(screen.getByText(/makes 1 serving$/i)).toBeInTheDocument()
  })
})
