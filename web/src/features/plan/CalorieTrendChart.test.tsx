import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { CalorieTrendChart } from '@/features/plan/CalorieTrendChart'
import type { DayPlan } from '@/api/types'

const DAYS: DayPlan[] = [
  { day: 'Monday', meals: [], total_calories: 1800, total_protein: 120, total_carbs: 150 },
  { day: 'Tuesday', meals: [], total_calories: 2100, total_protein: 130, total_carbs: 180 },
]

describe('CalorieTrendChart', () => {
  it('renders nothing when there is no plan data', () => {
    const { container } = render(<CalorieTrendChart days={[]} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('renders a heading and a chart when plan days are present', () => {
    const { container } = render(<CalorieTrendChart days={DAYS} />)
    expect(screen.getByText('Calories this week')).toBeInTheDocument()
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument()
  })
})
