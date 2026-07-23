import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { MealsPage } from '@/features/meals/MealsPage'
import type { AddMealRequest } from '@/api/types'

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const MEALS = [
  {
    name: 'Chicken Bowl',
    version: '2024-01-01',
    category: 'Dinner',
    servings: 2,
    macros: { calories: 500, protein: 35, carbs: 40, fat: 12 },
    ingredients: [
      { name: 'Chicken', serving: '6 oz', calories: 280, protein: 38, carbs: 0, fat: 12 },
      { name: 'Rice', serving: '1 cup', calories: 200, protein: 4, carbs: 45, fat: 0 },
    ],
    instructions: ['Cook chicken', 'Serve with rice'],
    tags: ['high_protein'],
  },
]

function renderMealsPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <MealsPage />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('MealsPage', () => {
  it('renders meals from the search endpoint', async () => {
    server.use(http.get('http://localhost/api/meals/search', () => HttpResponse.json(MEALS)))
    renderMealsPage()
    await screen.findByText('Chicken Bowl')
    expect(screen.getByText('Dinner')).toBeInTheDocument()
    expect(screen.getByText('500')).toBeInTheDocument()
  })

  it('sends search_term param when user searches', async () => {
    let lastSearchTerm = ''
    server.use(
      http.get('http://localhost/api/meals/search', ({ request }) => {
        lastSearchTerm = new URL(request.url).searchParams.get('search_term') ?? ''
        return HttpResponse.json([])
      })
    )
    renderMealsPage()
    const input = await screen.findByPlaceholderText(/search/i)
    fireEvent.change(input, { target: { value: 'salad' } })
    fireEvent.click(screen.getByRole('button', { name: /^search$/i }))
    await waitFor(() => expect(lastSearchTerm).toBe('salad'))
  })

  it('shows add-meal form when Add Meal button is clicked', async () => {
    server.use(http.get('http://localhost/api/meals/search', () => HttpResponse.json([])))
    renderMealsPage()
    await screen.findByRole('button', { name: /add meal/i })
    fireEvent.click(screen.getByRole('button', { name: /add meal/i }))
    expect(screen.getByLabelText(/meal name/i)).toBeInTheDocument()
  })

  it('opens a detail dialog when a meal row is clicked', async () => {
    server.use(http.get('http://localhost/api/meals/search', () => HttpResponse.json(MEALS)))
    renderMealsPage()
    fireEvent.click(await screen.findByText('Chicken Bowl'))
    expect(await screen.findByText(/makes 2 servings/i)).toBeInTheDocument()
    expect(screen.getByText('Cook chicken')).toBeInTheDocument()
  })

  it('sends servings in the add-meal payload', async () => {
    let body: AddMealRequest | null = null
    server.use(
      http.get('http://localhost/api/meals/search', () => HttpResponse.json([])),
      http.post('http://localhost/api/meals/add', async ({ request }) => {
        body = (await request.json()) as AddMealRequest
        return HttpResponse.json({
          success: true, meal_name: 'X', newly_added: [], category: 'Dinner', message: 'ok',
        })
      })
    )
    renderMealsPage()
    fireEvent.click(await screen.findByRole('button', { name: /add meal/i }))
    fireEvent.change(screen.getByLabelText(/meal name/i), { target: { value: 'X' } })
    fireEvent.change(screen.getByLabelText(/ingredient 1 name/i), { target: { value: 'Egg' } })
    fireEvent.change(screen.getByLabelText(/instructions/i), { target: { value: 'Cook' } })
    fireEvent.change(screen.getByLabelText(/servings/i), { target: { value: '4' } })
    fireEvent.click(screen.getByRole('button', { name: /save meal/i }))
    await waitFor(() => expect(body).not.toBeNull())
    expect(body!.servings).toBe(4)
  })

  it('sends structured per-ingredient serving sizes and macros in the add-meal payload', async () => {
    let body: AddMealRequest | null = null
    server.use(
      http.get('http://localhost/api/meals/search', () => HttpResponse.json([])),
      http.post('http://localhost/api/meals/add', async ({ request }) => {
        body = (await request.json()) as AddMealRequest
        return HttpResponse.json({
          success: true, meal_name: 'X', newly_added: [], category: 'Dinner', message: 'ok',
        })
      })
    )
    renderMealsPage()
    fireEvent.click(await screen.findByRole('button', { name: /add meal/i }))
    fireEvent.change(screen.getByLabelText(/meal name/i), { target: { value: 'X' } })
    fireEvent.change(screen.getByLabelText(/instructions/i), { target: { value: 'Cook' } })

    fireEvent.change(screen.getByLabelText(/ingredient 1 name/i), { target: { value: 'Chicken' } })
    fireEvent.change(screen.getByLabelText(/ingredient 1 serving/i), { target: { value: '6 oz' } })
    fireEvent.change(screen.getByLabelText(/ingredient 1 calories/i), { target: { value: '280' } })
    fireEvent.change(screen.getByLabelText(/ingredient 1 protein/i), { target: { value: '38' } })
    fireEvent.change(screen.getByLabelText(/ingredient 1 carbs/i), { target: { value: '0' } })
    fireEvent.change(screen.getByLabelText(/ingredient 1 fat/i), { target: { value: '12' } })

    fireEvent.click(screen.getByRole('button', { name: /add ingredient/i }))
    fireEvent.change(screen.getByLabelText(/ingredient 2 name/i), { target: { value: 'Rice' } })
    fireEvent.change(screen.getByLabelText(/ingredient 2 serving/i), { target: { value: '1 cup' } })
    fireEvent.change(screen.getByLabelText(/ingredient 2 calories/i), { target: { value: '200' } })

    fireEvent.click(screen.getByRole('button', { name: /save meal/i }))
    await waitFor(() => expect(body).not.toBeNull())
    expect(body!.ingredients).toEqual([
      { name: 'Chicken', serving: '6 oz', calories: 280, protein: 38, carbs: 0, fat: 12 },
      { name: 'Rice', serving: '1 cup', calories: 200, protein: 0, carbs: 0, fat: 0 },
    ])
  })

  it('removes an ingredient row and keeps at least one row', async () => {
    server.use(http.get('http://localhost/api/meals/search', () => HttpResponse.json([])))
    renderMealsPage()
    fireEvent.click(await screen.findByRole('button', { name: /add meal/i }))

    fireEvent.click(screen.getByRole('button', { name: /add ingredient/i }))
    expect(screen.getByLabelText(/ingredient 2 name/i)).toBeInTheDocument()

    const removeButtons = screen.getAllByRole('button', { name: /^remove$/i })
    fireEvent.click(removeButtons[1])
    expect(screen.queryByLabelText(/ingredient 2 name/i)).not.toBeInTheDocument()

    expect(screen.getAllByRole('button', { name: /^remove$/i })[0]).toBeDisabled()
  })
})
