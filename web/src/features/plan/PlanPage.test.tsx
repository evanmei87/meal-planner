import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { PlanPage } from './PlanPage'

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const PLAN_DATA = {
  plan_id: 'test-123',
  plan: [
    {
      day: 'Monday',
      meals: [
        {
          name: 'Oatmeal',
          calories: 400,
          macros: { protein: 15, carbs: 60, fat: 8 },
          ingredients: ['Oats', 'Milk'],
        },
      ],
      total_calories: 400,
      total_protein: 15,
      total_carbs: 60,
    },
    {
      day: 'Tuesday',
      meals: [
        {
          name: 'Chicken Bowl',
          calories: 550,
          macros: { protein: 40, carbs: 45, fat: 15 },
          ingredients: ['Chicken', 'Rice'],
        },
      ],
      total_calories: 550,
      total_protein: 40,
      total_carbs: 45,
    },
  ],
  grocery_list: [{ item: 'Oats', quantity: 1, unit: 'cup', category: 'grain' }],
  status: 'success',
}

function renderPlanPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/plan']}>
        <Routes>
          <Route path="/plan" element={<PlanPage />} />
          <Route path="/meals/:name" element={<div data-testid="meal-detail">Meal Detail</div>} />
          <Route path="/groceries" element={<div data-testid="groceries">Groceries</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('PlanPage', () => {
  it('shows "no plan yet" message when plan is empty', async () => {
    server.use(
      http.get('http://localhost/api/plan/', () =>
        HttpResponse.json({ plan_id: 'x', plan: [], grocery_list: [], status: 'success' })
      )
    )
    renderPlanPage()
    await screen.findByText(/no plan yet/i)
  })

  it('renders day buttons and first day meals after loading', async () => {
    server.use(http.get('http://localhost/api/plan/', () => HttpResponse.json(PLAN_DATA)))
    renderPlanPage()
    await screen.findByText('Monday')
    expect(screen.getByText('Tuesday')).toBeInTheDocument()
    expect(screen.getByText('Oatmeal')).toBeInTheDocument()
    expect(screen.getByText(/400 kcal/)).toBeInTheDocument()
  })

  it('switches displayed meals when a different day is selected', async () => {
    server.use(http.get('http://localhost/api/plan/', () => HttpResponse.json(PLAN_DATA)))
    renderPlanPage()
    await screen.findByText('Oatmeal')
    fireEvent.click(screen.getByRole('button', { name: 'Tuesday' }))
    expect(screen.getByText('Chicken Bowl')).toBeInTheDocument()
    expect(screen.queryByText('Oatmeal')).not.toBeInTheDocument()
  })

  it('meal name is a link pointing to /meals/:encodedName', async () => {
    server.use(http.get('http://localhost/api/plan/', () => HttpResponse.json(PLAN_DATA)))
    renderPlanPage()
    const link = await screen.findByRole('link', { name: 'Oatmeal' })
    expect(link.getAttribute('href')).toBe(`/meals/${encodeURIComponent('Oatmeal')}`)
  })

  it('shows grocery list link when grocery_list is non-empty', async () => {
    server.use(http.get('http://localhost/api/plan/', () => HttpResponse.json(PLAN_DATA)))
    renderPlanPage()
    await screen.findByText(/grocery list/i)
  })

  it('calls generate endpoint on button click', async () => {
    let generateCalled = false
    server.use(
      http.get('http://localhost/api/plan/', () => HttpResponse.json(PLAN_DATA)),
      http.post('http://localhost/api/plan/generate', () => {
        generateCalled = true
        return HttpResponse.json(PLAN_DATA)
      })
    )
    renderPlanPage()
    await screen.findByRole('button', { name: /generate plan/i })
    fireEvent.click(screen.getByRole('button', { name: /generate plan/i }))
    await waitFor(() => expect(generateCalled).toBe(true))
  })
})
