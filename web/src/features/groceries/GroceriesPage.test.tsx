import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { GroceriesPage } from '@/features/groceries/GroceriesPage'

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const STATE = {
  current_day: 'Monday',
  plan_id: 'x',
  plan: [],
  grocery_list: [{ item: 'Chicken', quantity: 2, unit: 'lbs', category: 'protein' }],
  missing_macros: [],
  grocery_inventory: [{ standardized_item: 'Spinach', quantity: 1, unit: 'bag' }],
  unmatched_groceries: [],
  inventory_usage: { used: [], unused: [], supplemental: [] },
}

const PARSE_RESULT = {
  items: [
    {
      raw_phrase: '2 lbs chicken',
      standardized_item: 'Chicken',
      quantity: 2,
      unit: 'lbs',
      match: 'Chicken, broilers',
      confidence_score: 0.86,
      confidence_level: 'high',
      status: 'auto',
    },
  ],
  saved_count: 1,
  review_count: 0,
}

function renderGroceriesPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <GroceriesPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('GroceriesPage', () => {
  it('shows grocery list items from state', async () => {
    server.use(http.get('http://localhost/api/state/', () => HttpResponse.json(STATE)))
    renderGroceriesPage()
    await screen.findByText('Chicken')
  })

  it('shows inventory items from state', async () => {
    server.use(http.get('http://localhost/api/state/', () => HttpResponse.json(STATE)))
    renderGroceriesPage()
    await screen.findByText('Spinach')
  })

  it('submits NL text and renders parse result table with confidence and status', async () => {
    server.use(
      http.get('http://localhost/api/state/', () => HttpResponse.json(STATE)),
      http.post('http://localhost/api/groceries/', () => HttpResponse.json(PARSE_RESULT))
    )
    renderGroceriesPage()
    await screen.findByText('Chicken')
    const input = screen.getByPlaceholderText(/chicken thighs/i)
    fireEvent.change(input, { target: { value: '2 lbs chicken' } })
    fireEvent.click(screen.getByRole('button', { name: /^add$/i }))
    await screen.findByText('2 lbs chicken')
    expect(screen.getByText('0.86')).toBeInTheDocument()
    expect(screen.getByText('auto')).toBeInTheDocument()
    expect(screen.getByText('Saved: 1 · Review/Manual: 0')).toBeInTheDocument()
  })

  it('invalidates state query after successful grocery add', async () => {
    let stateFetchCount = 0
    server.use(
      http.get('http://localhost/api/state/', () => {
        stateFetchCount++
        return HttpResponse.json(STATE)
      }),
      http.post('http://localhost/api/groceries/', () => HttpResponse.json(PARSE_RESULT))
    )
    renderGroceriesPage()
    await screen.findByText('Chicken')
    const input = screen.getByPlaceholderText(/chicken thighs/i)
    fireEvent.change(input, { target: { value: '2 lbs chicken' } })
    fireEvent.click(screen.getByRole('button', { name: /^add$/i }))
    await screen.findByText('2 lbs chicken')
    await waitFor(() => expect(stateFetchCount).toBeGreaterThan(1))
  })
})
