import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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

  it('renders preferences input pre-filled from stored state', async () => {
    server.use(
      http.get('http://localhost/api/state/', () =>
        HttpResponse.json({ ...STATE, preferences: 'high protein' })
      )
    )
    renderStatePage()
    const input = await screen.findByPlaceholderText(/e\.g\. no red meat/i)
    expect(input).toHaveValue('high protein')
  })

  it('Save button calls PUT /state/ with the current preferences value', async () => {
    let putBody: unknown = null
    server.use(
      http.get('http://localhost/api/state/', () =>
        HttpResponse.json({ ...STATE, preferences: 'vegetarian' })
      ),
      http.put('http://localhost/api/state/', async ({ request }) => {
        putBody = await request.json()
        return HttpResponse.json({ ...STATE, preferences: 'vegetarian' })
      })
    )
    renderStatePage()
    await screen.findByPlaceholderText(/e\.g\. no red meat/i)
    fireEvent.click(screen.getByRole('button', { name: /^save$/i }))
    await waitFor(() => expect(putBody).toMatchObject({ preferences: 'vegetarian' }))
  })

  it('shows Regenerate Plan button when plan_id is non-empty', async () => {
    server.use(
      http.get('http://localhost/api/state/', () => HttpResponse.json({ ...STATE, plan_id: 'abc-123' }))
    )
    renderStatePage()
    await screen.findByRole('button', { name: /regenerate plan/i })
  })

  it('hides Regenerate Plan button when plan_id is empty', async () => {
    server.use(
      http.get('http://localhost/api/state/', () => HttpResponse.json({ ...STATE, plan_id: '' }))
    )
    renderStatePage()
    await screen.findByText('Wednesday')
    expect(screen.queryByRole('button', { name: /regenerate plan/i })).not.toBeInTheDocument()
  })

  it('Regenerate Plan button calls POST /plan/generate with stored preferences', async () => {
    let generateBody: unknown = null
    server.use(
      http.get('http://localhost/api/state/', () =>
        HttpResponse.json({ ...STATE, plan_id: 'abc-123', preferences: 'high protein' })
      ),
      http.post('http://localhost/api/plan/generate', async ({ request }) => {
        generateBody = await request.json()
        return HttpResponse.json({
          plan_id: 'abc-123',
          plan: [],
          grocery_list: [],
          status: 'success',
        })
      })
    )
    renderStatePage()
    fireEvent.click(await screen.findByRole('button', { name: /regenerate plan/i }))
    await waitFor(() => expect(generateBody).toMatchObject({ preferences: 'high protein' }))
  })
})
