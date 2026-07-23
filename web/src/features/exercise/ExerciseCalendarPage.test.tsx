import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ExerciseCalendarPage } from './ExerciseCalendarPage'

describe('ExerciseCalendarPage', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-24T12:00:00-04:00')) // a Wednesday
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders all 7 days of the current week', () => {
    render(<ExerciseCalendarPage />)
    expect(screen.getAllByRole('button')).toHaveLength(7)
    expect(screen.getByRole('button', { name: 'Mon, Jun 22' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sun, Jun 28' })).toBeInTheDocument()
  })

  it('highlights today with the primary token', () => {
    render(<ExerciseCalendarPage />)
    const today = screen.getByRole('button', { name: 'Wed, Jun 24' })
    expect(today.className).toContain('bg-primary')

    const notToday = screen.getByRole('button', { name: 'Mon, Jun 22' })
    expect(notToday.className).not.toContain('bg-primary')
  })

  it('shows a placeholder for today by default', () => {
    render(<ExerciseCalendarPage />)
    expect(screen.getByText('Exercises for 2026-06-24')).toBeInTheDocument()
  })

  it('updates the placeholder when a different day is clicked', () => {
    render(<ExerciseCalendarPage />)
    fireEvent.click(screen.getByRole('button', { name: 'Mon, Jun 22' }))
    expect(screen.getByText('Exercises for 2026-06-22')).toBeInTheDocument()
    expect(screen.queryByText('Exercises for 2026-06-24')).not.toBeInTheDocument()
  })
})
