import { fireEvent, render, screen } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ExerciseCalendarPage } from './ExerciseCalendarPage'
import type { AddExerciseRequest, ExerciseWeekResponse } from '@/api/types'

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const WEEK_START = '2026-06-22'
const WEEK_DATES = ['2026-06-22', '2026-06-23', '2026-06-24', '2026-06-25', '2026-06-26', '2026-06-27', '2026-06-28']
const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

function emptyWeek(): ExerciseWeekResponse {
  return {
    week_start: WEEK_START,
    days: WEEK_DATES.map((date, i) => ({
      date,
      day_name: DAY_NAMES[i],
      exercises: [],
      total_calories: 0,
    })),
  }
}

function renderExercisePage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <ExerciseCalendarPage />
    </QueryClientProvider>
  )
}

describe('ExerciseCalendarPage', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-06-24T12:00:00-04:00')) // a Wednesday
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders all 7 days of the current week', async () => {
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(emptyWeek())))
    renderExercisePage()
    await screen.findByRole('button', { name: 'Wed, Jun 24' })
    expect(screen.getAllByRole('button')).toHaveLength(8) // 7 days + Add Exercise
    expect(screen.getByRole('button', { name: 'Mon, Jun 22' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sun, Jun 28' })).toBeInTheDocument()
  })

  it('highlights today with the primary token', async () => {
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(emptyWeek())))
    renderExercisePage()
    const today = await screen.findByRole('button', { name: 'Wed, Jun 24' })
    expect(today.className).toContain('bg-primary')

    const notToday = screen.getByRole('button', { name: 'Mon, Jun 22' })
    expect(notToday.className).not.toContain('bg-primary')
  })

  it('shows a placeholder for a day with no exercises', async () => {
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(emptyWeek())))
    renderExercisePage()
    await screen.findByText('No exercises logged for this day.')
  })

  it('updates the selected day when a different day is clicked', async () => {
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(emptyWeek())))
    renderExercisePage()
    await screen.findByText('Exercises for 2026-06-24')
    fireEvent.click(screen.getByRole('button', { name: 'Mon, Jun 22' }))
    expect(screen.getByText('Exercises for 2026-06-22')).toBeInTheDocument()
    expect(screen.queryByText('Exercises for 2026-06-24')).not.toBeInTheDocument()
  })

  it('renders a day badge and its exercises with calories', async () => {
    const week = emptyWeek()
    week.days[2] = {
      date: '2026-06-24',
      day_name: 'Wednesday',
      exercises: [
        { id: 'ex1', type: 'running', distance_miles: 3.1, duration_minutes: 28, calories: 320, notes: 'Easy pace' },
        { id: 'ex2', type: 'running', distance_miles: 5, duration_minutes: 45, calories: 500, notes: null },
      ],
      total_calories: 820,
    }
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(week)))
    renderExercisePage()

    await screen.findByText('2 exercises · 820 cal')
    expect(screen.getByText('3.1 mi · 28 min · 320 cal')).toBeInTheDocument()
    expect(screen.getByText(/Easy pace/)).toBeInTheDocument()
    expect(screen.getByText('5 mi · 45 min · 500 cal')).toBeInTheDocument()
  })

  it('submitting the form posts a new exercise and it appears after refetch', async () => {
    let week = emptyWeek()
    server.use(
      http.get('http://localhost/api/exercises/', () => HttpResponse.json(week)),
      http.post('http://localhost/api/exercises/', async ({ request }) => {
        const body = (await request.json()) as {
          date: string
          distance_miles: number
          duration_minutes: number
          notes?: string
        }
        const newExercise = {
          id: 'new-1',
          type: 'running' as const,
          distance_miles: body.distance_miles,
          duration_minutes: body.duration_minutes,
          calories: 400,
          notes: body.notes ?? null,
        }
        week = {
          ...week,
          days: week.days.map((d) =>
            d.date === body.date
              ? { ...d, exercises: [...d.exercises, newExercise], total_calories: d.total_calories + newExercise.calories }
              : d
          ),
        }
        return HttpResponse.json(newExercise)
      })
    )

    renderExercisePage()
    await screen.findByText('No exercises logged for this day.')

    fireEvent.change(screen.getByLabelText('Distance (mi)'), { target: { value: '3.1' } })
    fireEvent.change(screen.getByLabelText('Duration (min)'), { target: { value: '28' } })
    fireEvent.click(screen.getByRole('button', { name: /add exercise/i }))

    await screen.findByText('3.1 mi · 28 min · 400 cal')
    expect(screen.queryByText('No exercises logged for this day.')).not.toBeInTheDocument()
  })

  it('submitting a walking exercise posts distance and no sets/reps', async () => {
    let week = emptyWeek()
    let postedBody: AddExerciseRequest | undefined
    server.use(
      http.get('http://localhost/api/exercises/', () => HttpResponse.json(week)),
      http.post('http://localhost/api/exercises/', async ({ request }) => {
        const body = (await request.json()) as AddExerciseRequest
        postedBody = body
        const newExercise = {
          id: 'new-walk',
          type: 'walking' as const,
          distance_miles: body.distance_miles,
          duration_minutes: body.duration_minutes,
          calories: 150,
          notes: null,
        }
        week = {
          ...week,
          days: week.days.map((d) =>
            d.date === body.date
              ? { ...d, exercises: [...d.exercises, newExercise], total_calories: d.total_calories + newExercise.calories }
              : d
          ),
        }
        return HttpResponse.json(newExercise)
      })
    )

    renderExercisePage()
    await screen.findByText('No exercises logged for this day.')

    fireEvent.change(screen.getByLabelText('Type'), { target: { value: 'walking' } })
    fireEvent.change(screen.getByLabelText('Distance (mi)'), { target: { value: '2' } })
    fireEvent.change(screen.getByLabelText('Duration (min)'), { target: { value: '30' } })
    fireEvent.click(screen.getByRole('button', { name: /add exercise/i }))

    await screen.findByText('2 mi · 30 min · 150 cal')
    expect(postedBody).toMatchObject({ type: 'walking', distance_miles: 2, duration_minutes: 30 })
    expect(postedBody?.sets).toBeUndefined()
    expect(postedBody?.reps).toBeUndefined()
  })

  it('submitting a strength exercise posts sets/reps and no distance', async () => {
    let week = emptyWeek()
    let postedBody: AddExerciseRequest | undefined
    server.use(
      http.get('http://localhost/api/exercises/', () => HttpResponse.json(week)),
      http.post('http://localhost/api/exercises/', async ({ request }) => {
        const body = (await request.json()) as AddExerciseRequest
        postedBody = body
        const newExercise = {
          id: 'new-strength',
          type: 'strength' as const,
          sets: body.sets,
          reps: body.reps,
          duration_minutes: body.duration_minutes,
          calories: 180,
          notes: null,
        }
        week = {
          ...week,
          days: week.days.map((d) =>
            d.date === body.date
              ? { ...d, exercises: [...d.exercises, newExercise], total_calories: d.total_calories + newExercise.calories }
              : d
          ),
        }
        return HttpResponse.json(newExercise)
      })
    )

    renderExercisePage()
    await screen.findByText('No exercises logged for this day.')

    fireEvent.change(screen.getByLabelText('Type'), { target: { value: 'strength' } })
    expect(screen.queryByLabelText('Distance (mi)')).not.toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Sets'), { target: { value: '3' } })
    fireEvent.change(screen.getByLabelText('Reps'), { target: { value: '10' } })
    fireEvent.change(screen.getByLabelText('Duration (min)'), { target: { value: '20' } })
    fireEvent.click(screen.getByRole('button', { name: /add exercise/i }))

    await screen.findByText('3 sets × 10 reps · 20 min · 180 cal')
    expect(postedBody).toMatchObject({ type: 'strength', sets: 3, reps: 10, duration_minutes: 20 })
    expect(postedBody?.distance_miles).toBeUndefined()
  })

  it('editing an exercise pre-fills the form and the row reflects the new values after save', async () => {
    let week = emptyWeek()
    week.days[2] = {
      date: '2026-06-24',
      day_name: 'Wednesday',
      exercises: [
        { id: 'ex1', type: 'running', distance_miles: 3.1, duration_minutes: 28, calories: 320, notes: 'Easy pace' },
      ],
      total_calories: 320,
    }
    server.use(
      http.get('http://localhost/api/exercises/', () => HttpResponse.json(week)),
      http.put('http://localhost/api/exercises/ex1', async ({ request }) => {
        const body = (await request.json()) as {
          distance_miles: number
          duration_minutes: number
          notes?: string
        }
        const updated = {
          id: 'ex1',
          type: 'running' as const,
          distance_miles: body.distance_miles,
          duration_minutes: body.duration_minutes,
          calories: 600,
          notes: body.notes ?? null,
        }
        week = {
          ...week,
          days: week.days.map((d) =>
            d.date === '2026-06-24' ? { ...d, exercises: [updated], total_calories: 600 } : d
          ),
        }
        return HttpResponse.json(updated)
      })
    )

    renderExercisePage()
    await screen.findByText('3.1 mi · 28 min · 320 cal')

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))

    expect(screen.getByLabelText('Distance (mi)')).toHaveValue(3.1)
    expect(screen.getByLabelText('Duration (min)')).toHaveValue(28)
    expect(screen.getByLabelText('Notes (optional)')).toHaveValue('Easy pace')
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Distance (mi)'), { target: { value: '6' } })
    fireEvent.change(screen.getByLabelText('Duration (min)'), { target: { value: '55' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save Changes' }))

    await screen.findByText('6 mi · 55 min · 600 cal')
    expect(screen.queryByText('3.1 mi · 28 min · 320 cal')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument()
  })

  it('cancelling an edit returns the form to add mode without changing the row', async () => {
    const week = emptyWeek()
    week.days[2] = {
      date: '2026-06-24',
      day_name: 'Wednesday',
      exercises: [
        { id: 'ex1', type: 'running', distance_miles: 3.1, duration_minutes: 28, calories: 320, notes: null },
      ],
      total_calories: 320,
    }
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(week)))

    renderExercisePage()
    await screen.findByText('3.1 mi · 28 min · 320 cal')

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.queryByRole('button', { name: 'Cancel' })).not.toBeInTheDocument()
    expect(screen.getByLabelText('Distance (mi)')).toHaveValue(null)
    expect(screen.getByText('3.1 mi · 28 min · 320 cal')).toBeInTheDocument()
  })

  it('removing an exercise after confirming removes the row', async () => {
    let week = emptyWeek()
    week.days[2] = {
      date: '2026-06-24',
      day_name: 'Wednesday',
      exercises: [
        { id: 'ex1', type: 'running', distance_miles: 3.1, duration_minutes: 28, calories: 320, notes: null },
      ],
      total_calories: 320,
    }
    server.use(
      http.get('http://localhost/api/exercises/', () => HttpResponse.json(week)),
      http.delete('http://localhost/api/exercises/ex1', () => {
        week = { ...week, days: week.days.map((d) => (d.date === '2026-06-24' ? { ...d, exercises: [], total_calories: 0 } : d)) }
        return new HttpResponse(null, { status: 204 })
      })
    )
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    renderExercisePage()
    await screen.findByText('3.1 mi · 28 min · 320 cal')

    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))

    expect(window.confirm).toHaveBeenCalledWith('Remove this exercise?')
    await screen.findByText('No exercises logged for this day.')
  })

  it('does not remove the exercise when the confirmation is declined', async () => {
    const week = emptyWeek()
    week.days[2] = {
      date: '2026-06-24',
      day_name: 'Wednesday',
      exercises: [
        { id: 'ex1', type: 'running', distance_miles: 3.1, duration_minutes: 28, calories: 320, notes: null },
      ],
      total_calories: 320,
    }
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(week)))
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    renderExercisePage()
    await screen.findByText('3.1 mi · 28 min · 320 cal')

    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))

    expect(window.confirm).toHaveBeenCalledWith('Remove this exercise?')
    expect(screen.getByText('3.1 mi · 28 min · 320 cal')).toBeInTheDocument()
  })
})
