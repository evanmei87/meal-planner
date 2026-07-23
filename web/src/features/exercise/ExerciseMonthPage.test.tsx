import { render, screen } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { ExerciseMonthPage } from './ExerciseMonthPage'
import type { ExerciseDayPlan, ExerciseMonthResponse } from '@/api/types'

const navigateMock = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => navigateMock }
})

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const MONTH = '2026-06' // June 2026: 30 days, starting on a Monday

function emptyMonth(): ExerciseMonthResponse {
  const days: ExerciseDayPlan[] = Array.from({ length: 30 }, (_, i) => ({
    date: `2026-06-${String(i + 1).padStart(2, '0')}`,
    day_name: '',
    exercises: [],
    total_calories: 0,
  }))
  return { month: MONTH, days }
}

function renderMonthPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ExerciseMonthPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('ExerciseMonthPage', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-06-24T12:00:00-04:00')) // a Wednesday in June 2026
    navigateMock.mockClear()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders one day cell for every day in the month', async () => {
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(emptyMonth())))
    renderMonthPage()

    await screen.findByRole('button', { name: '1' })
    for (let day = 1; day <= 30; day++) {
      expect(screen.getByRole('button', { name: String(day) })).toBeInTheDocument()
    }
    // June 2026 has no day 31.
    expect(screen.queryByRole('button', { name: '31' })).not.toBeInTheDocument()
  })

  it('shows the exercise count and calories for a day with exercises', async () => {
    const month = emptyMonth()
    month.days[14] = {
      date: '2026-06-15',
      day_name: 'Monday',
      exercises: [
        { id: 'ex1', type: 'running', distance_miles: 3.1, duration_minutes: 28, calories: 320, notes: null, order: 0 },
      ],
      total_calories: 320,
    }
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(month)))
    renderMonthPage()

    await screen.findByText('1 ex · 320 cal')
  })

  it('shows no badge for a day with no exercises', async () => {
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(emptyMonth())))
    renderMonthPage()

    await screen.findByRole('button', { name: '1' })
    expect(screen.queryByText(/ex ·/)).not.toBeInTheDocument()
  })

  it('navigates to the weekly view anchored on the Monday of the clicked day', async () => {
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(emptyMonth())))
    renderMonthPage()

    const day24 = await screen.findByRole('button', { name: '24' }) // a Wednesday
    day24.click()

    expect(navigateMock).toHaveBeenCalledWith('/exercise?week_start=2026-06-22')
  })

  it('links back to the weekly view', async () => {
    server.use(http.get('http://localhost/api/exercises/', () => HttpResponse.json(emptyMonth())))
    renderMonthPage()

    await screen.findByRole('button', { name: '1' })
    expect(screen.getByRole('link', { name: 'Week view' })).toHaveAttribute('href', '/exercise')
  })
})
