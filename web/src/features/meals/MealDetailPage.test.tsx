import { render, screen } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { MealDetailPage } from '@/features/meals/MealDetailPage'
import type { MealItem } from '@/api/types'

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const SAVED_MEAL = {
  name: 'Chicken Bowl',
  version: '2024-01-01',
  category: 'Dinner',
  servings: 1,
  macros: { calories: 500, protein: 35, carbs: 40, fat: 12 },
  ingredients: ['Chicken', 'Rice'],
  instructions: ['Cook chicken', 'Serve with rice'],
  tags: [],
}

function renderDetail(encodedName: string, locationState?: unknown) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter
        initialEntries={[{ pathname: `/meals/${encodedName}`, state: locationState }]}
      >
        <Routes>
          <Route path="/meals/:name" element={<MealDetailPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('MealDetailPage', () => {
  it('shows full saved meal details when name matches a saved meal', async () => {
    server.use(
      http.get('http://localhost/api/meals/', () => HttpResponse.json([SAVED_MEAL]))
    )
    renderDetail(encodeURIComponent('Chicken Bowl'))
    await screen.findByText('Chicken Bowl')
    expect(screen.getByText('Cook chicken')).toBeInTheDocument()
    expect(screen.getByText('Dinner')).toBeInTheDocument()
  })

  it('shows plan meal fallback with "not in saved library" notice when no saved meal matches', async () => {
    server.use(http.get('http://localhost/api/meals/', () => HttpResponse.json([])))
    const planMeal: MealItem = {
      name: 'Mystery Dish',
      calories: 300,
      macros: { protein: 20, carbs: 30, fat: 10 },
      ingredients: ['Egg'],
    }
    renderDetail(encodeURIComponent('Mystery Dish'), { planMeal })
    await screen.findByText('Mystery Dish')
    expect(screen.getByText(/not in your saved library/i)).toBeInTheDocument()
    expect(screen.getByText('Egg')).toBeInTheDocument()
  })

  it('shows not-found message when no saved meal and no plan meal in location state', async () => {
    server.use(http.get('http://localhost/api/meals/', () => HttpResponse.json([])))
    renderDetail(encodeURIComponent('Ghost Meal'))
    await screen.findByText(/not found/i)
  })
})
