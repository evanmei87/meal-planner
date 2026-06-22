import { render, screen } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { StatePage } from './StatePage'

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const STATE = {
  current_day: 'Wednesday',
  plan_id: 'abc-123',
  plan: [],
  grocery_list: [],
  missing_macros: ['mystery_spice'],
  grocery_inventory: [],
  unmatched_groceries: [{ raw_phrase: 'premium saffron', standardized_item: 'saffron', source: 'specialty' }],
  inventory_usage: { used: ['chicken'], unused: ['spinach'], supplemental: ['quinoa'] },
}

function renderStatePage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <StatePage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('StatePage', () => {
  it('shows current day and plan id', async () => {
    server.use(http.get('http://localhost/api/state/', () => HttpResponse.json(STATE)))
    renderStatePage()
    await screen.findByText('Wednesday')
    expect(screen.getByText('abc-123')).toBeInTheDocument()
  })

  it('shows inventory usage sections with items', async () => {
    server.use(http.get('http://localhost/api/state/', () => HttpResponse.json(STATE)))
    renderStatePage()
    await screen.findByText('chicken')
    expect(screen.getByText('spinach')).toBeInTheDocument()
    expect(screen.getByText('quinoa')).toBeInTheDocument()
  })

  it('shows unmatched groceries table', async () => {
    server.use(http.get('http://localhost/api/state/', () => HttpResponse.json(STATE)))
    renderStatePage()
    await screen.findByText('saffron')
  })
})
