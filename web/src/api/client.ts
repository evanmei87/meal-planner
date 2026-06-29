import type {
  AddMealRequest,
  AddMealResponse,
  AppState,
  GroceriesResponse,
  MealPlanRequest,
  MealPlanResponse,
  MealResponse,
  SearchParams,
} from '@/api/types'

const BASE = '/api'

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const apiKey = import.meta.env.VITE_API_KEY ?? ''
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
      ...init?.headers,
    },
  })
  if (!res.ok) {
    const message =
      res.status === 401
        ? 'Invalid API key — check VITE_API_KEY in web/.env'
        : `Request failed: ${res.status}`
    throw new ApiError(res.status, message)
  }
  return res.json() as Promise<T>
}

function buildQuery(params?: Record<string, unknown>): string {
  if (!params) return ''
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join('&')
  return qs ? `?${qs}` : ''
}

export const api = {
  plan: {
    get: () => request<MealPlanResponse>('/plan/'),
    generate: (body: MealPlanRequest) =>
      request<MealPlanResponse>('/plan/generate', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
  },
  meals: {
    list: (params?: { category?: string; search?: string }) =>
      request<MealResponse[]>(`/meals/${buildQuery(params as Record<string, unknown>)}`),
    search: (params: SearchParams) =>
      request<MealResponse[]>(`/meals/search${buildQuery(params as Record<string, unknown>)}`),
    add: (body: AddMealRequest) =>
      request<AddMealResponse>('/meals/add', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
  },
  state: {
    get: () => request<AppState>('/state/'),
    update: (body: Partial<AppState>) =>
      request<AppState>('/state/', {
        method: 'PUT',
        body: JSON.stringify(body),
      }),
  },
  groceries: {
    add: (text: string) =>
      request<GroceriesResponse>('/groceries/', {
        method: 'POST',
        body: JSON.stringify({ text }),
      }),
  },
}
