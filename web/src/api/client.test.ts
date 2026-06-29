import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { api, ApiError } from '@/api/client'

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const EMPTY_PLAN = { plan_id: 'x', plan: [], grocery_list: [], status: 'success' }

describe('api.plan.get', () => {
  it('injects X-API-Key header from VITE_API_KEY env', async () => {
    let capturedKey = ''
    server.use(
      http.get('http://localhost/api/plan/', ({ request }) => {
        capturedKey = request.headers.get('X-API-Key') ?? ''
        return HttpResponse.json(EMPTY_PLAN)
      })
    )
    await api.plan.get()
    expect(capturedKey).toBe(import.meta.env.VITE_API_KEY ?? '')
  })

  it('throws ApiError with friendly message on 401', async () => {
    server.use(
      http.get('http://localhost/api/plan/', () =>
        HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
      )
    )
    await expect(api.plan.get()).rejects.toThrow(
      'Invalid API key — check VITE_API_KEY in web/.env'
    )
  })

  it('throws ApiError with status on 500', async () => {
    server.use(
      http.get('http://localhost/api/plan/', () =>
        HttpResponse.json({ detail: 'server error' }, { status: 500 })
      )
    )
    const err = await api.plan.get().catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(500)
  })
})

describe('api.meals.list', () => {
  it('returns parsed JSON array', async () => {
    const meal = { name: 'Oatmeal', version: '1', category: 'Breakfast', macros: { calories: 300, protein: 10, carbs: 50, fat: 5 }, ingredients: [], instructions: [], tags: [] }
    server.use(http.get('http://localhost/api/meals/', () => HttpResponse.json([meal])))
    const result = await api.meals.list()
    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('Oatmeal')
  })
})
