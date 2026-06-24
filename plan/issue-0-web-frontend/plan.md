# Web Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a React + Vite + TypeScript SPA in `web/` that consumes the existing FastAPI backend, plus one new `POST /groceries` backend endpoint.

**Architecture:** Feature-based React Router pages (`/plan`, `/meals`, `/meals/:name`, `/groceries`, `/state`) backed by TanStack Query hooks. A single typed `api/client.ts` injects the `X-API-Key` header and maps errors to `ApiError`. The backend addition is a single new FastAPI router that reuses the existing `tools/` layer — no direct file I/O in the endpoint.

**Tech Stack:** React 18, Vite 6, TypeScript 5, Tailwind CSS 3, React Router 6, TanStack Query 5, Vitest 2, React Testing Library 16, MSW 2, FastAPI (Python, existing)

## Global Constraints

- All frontend files live under `web/`. Never add frontend files to the Python `src/` tree.
- Components never call `fetch` directly — always go through `api/client.ts`.
- The new `POST /groceries` endpoint must call `parse_ingredients`, `get_ingredient_metadata`, `add_inventory_items`, `add_unmatched_items` from the existing `src/tools/` layer; it must not read or write `state.json` directly.
- All new backend routes are registered behind `Security(get_api_key)` in `src/api/main.py`.
- Query key for the plan: `['plan']`. For meals list: `['meals']`. For search: `['meals', 'search', params]`. For state: `['state']`. Consistent across all files.
- MSW test handlers use full URLs: `http://localhost/api/<path>` (jsdom resolves relative fetch paths against `http://localhost`).
- Run backend tests from repo root: `uv run pytest tests/ -q`. Run frontend tests from `web/`: `npm test`.

---

### Task 1: POST /groceries backend endpoint

**Files:**
- Modify: `src/api/models.py`
- Create: `src/api/endpoints/groceries.py`
- Modify: `src/api/main.py`
- Create: `tests/test_api/test_groceries.py`

**Interfaces:**
- Consumes: `parse_ingredients(text: str) -> list[dict]`, `get_ingredient_metadata(item: dict) -> dict`, `add_inventory_items(items: list[dict]) -> dict`, `add_unmatched_items(items: list[dict])` from `src/tools/`
- Produces: `POST /groceries` → `GroceriesResponse` (used by `web/src/api/client.ts` in Task 3)

- [ ] **Step 1: Add Pydantic models to `src/api/models.py`**

Append at the end of the file:

```python
class GroceriesRequest(BaseModel):
    """Request to parse natural-language grocery text."""
    text: str = Field(..., min_length=1, description="Natural language grocery description")


class GroceryParseResult(BaseModel):
    """Single parsed grocery item row."""
    raw_phrase: str
    standardized_item: str
    quantity: float
    unit: str
    match: str
    confidence_score: float
    confidence_level: str
    status: str  # "auto" | "review" | "manual"


class GroceriesResponse(BaseModel):
    """Response after parsing and saving grocery text."""
    items: List[GroceryParseResult]
    saved_count: int
    review_count: int
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_api/test_groceries.py`:

```python
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def api_key_headers():
    return {"X-API-Key": "dev-key-change-in-production"}


FAKE_INGREDIENT = {
    "raw_phrase": "2 lbs chicken thighs",
    "standardized_item": "chicken thighs",
    "quantity": 2.0,
    "unit": "lbs",
    "corgis_style_query": "Chicken thigh",
}

FAKE_META_AUTO = {
    **FAKE_INGREDIENT,
    "corgis_description": "Chicken thigh, meat only",
    "confidence_score": 0.86,
    "confidence_level": "high",
    "should_auto_save": True,
    "source": "corgis",
}

FAKE_META_MANUAL = {
    **FAKE_INGREDIENT,
    "raw_phrase": "arugula",
    "standardized_item": "arugula",
    "corgis_description": None,
    "confidence_score": 0.2,
    "confidence_level": "low",
    "should_auto_save": False,
    "source": "specialty",
}


def test_groceries_add_high_confidence_auto_saves(client, api_key_headers):
    with (
        patch("src.api.endpoints.groceries.parse_ingredients", return_value=[FAKE_INGREDIENT]),
        patch("src.api.endpoints.groceries.get_ingredient_metadata", return_value=FAKE_META_AUTO),
        patch("src.api.endpoints.groceries.add_inventory_items", return_value={"added": [FAKE_META_AUTO]}) as mock_add,
        patch("src.api.endpoints.groceries.add_unmatched_items") as mock_unmatched,
    ):
        response = client.post("/groceries", json={"text": "2 lbs chicken thighs"}, headers=api_key_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["saved_count"] == 1
    assert data["review_count"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["raw_phrase"] == "2 lbs chicken thighs"
    assert data["items"][0]["status"] == "auto"
    assert data["items"][0]["confidence_score"] == 0.86
    assert data["items"][0]["match"] == "Chicken thigh, meat only"
    mock_add.assert_called_once()
    mock_unmatched.assert_not_called()


def test_groceries_add_low_confidence_goes_to_unmatched(client, api_key_headers):
    with (
        patch("src.api.endpoints.groceries.parse_ingredients", return_value=[FAKE_INGREDIENT]),
        patch("src.api.endpoints.groceries.get_ingredient_metadata", return_value=FAKE_META_MANUAL),
        patch("src.api.endpoints.groceries.add_inventory_items") as mock_add,
        patch("src.api.endpoints.groceries.add_unmatched_items") as mock_unmatched,
    ):
        response = client.post("/groceries", json={"text": "arugula"}, headers=api_key_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["saved_count"] == 0
    assert data["review_count"] == 1
    assert data["items"][0]["status"] == "manual"
    mock_add.assert_not_called()
    mock_unmatched.assert_called_once()


def test_groceries_add_requires_valid_api_key(client):
    response = client.post("/groceries", json={"text": "chicken"}, headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_groceries_add_rejects_empty_text(client, api_key_headers):
    response = client.post("/groceries", json={"text": ""}, headers=api_key_headers)
    assert response.status_code == 422
```

- [ ] **Step 3: Run test to confirm it fails**

```bash
uv run pytest tests/test_api/test_groceries.py -q
```

Expected: 4 errors — `src.api.endpoints.groceries` does not exist.

- [ ] **Step 4: Create `src/api/endpoints/groceries.py`**

```python
from fastapi import APIRouter, HTTPException

from src.api.models import GroceriesRequest, GroceriesResponse, GroceryParseResult
from src.tools.food_processor import parse_ingredients, get_ingredient_metadata
from src.tools.grocery_inventory import add_inventory_items, add_unmatched_items

router = APIRouter(prefix="/groceries", tags=["Groceries"])


@router.post("/", response_model=GroceriesResponse)
async def add_groceries(request: GroceriesRequest):
    """Parse natural-language grocery text and save high-confidence items to inventory."""
    try:
        ingredients = parse_ingredients(request.text)
        items: list[GroceryParseResult] = []
        to_save: list[dict] = []
        unmatched: list[dict] = []

        for ingredient in ingredients:
            meta = get_ingredient_metadata(ingredient)
            status = _classify_status(meta)
            items.append(GroceryParseResult(
                raw_phrase=meta.get("raw_phrase", ""),
                standardized_item=meta.get("standardized_item", ""),
                quantity=float(meta.get("quantity", 0)),
                unit=meta.get("unit", ""),
                match=meta.get("corgis_description") or meta.get("source", ""),
                confidence_score=float(meta.get("confidence_score", 0.0)),
                confidence_level=meta.get("confidence_level", ""),
                status=status,
            ))
            if meta.get("should_auto_save") and meta.get("source") == "corgis":
                to_save.append(meta)
            else:
                unmatched.append(meta)

        saved_count = 0
        if to_save:
            result = add_inventory_items(to_save)
            saved_count = len(result.get("added", []))

        if unmatched:
            add_unmatched_items(unmatched)

        return GroceriesResponse(items=items, saved_count=saved_count, review_count=len(unmatched))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse groceries: {str(e)}")


def _classify_status(meta: dict) -> str:
    if meta.get("should_auto_save"):
        return "auto"
    if meta.get("source") == "specialty" or not meta.get("corgis_description"):
        return "manual"
    return "review"
```

- [ ] **Step 5: Register router in `src/api/main.py`**

Add import after the existing endpoint imports:
```python
from src.api.endpoints import meal_plan, meals, state, groceries
```

Add after the existing `app.include_router` calls:
```python
app.include_router(groceries.router, dependencies=[Security(get_api_key)])
```

- [ ] **Step 6: Run tests to confirm they pass**

```bash
uv run pytest tests/test_api/test_groceries.py -v
```

Expected: 4 passed.

- [ ] **Step 7: Run full test suite to confirm no regressions**

```bash
uv run pytest tests/ -q
```

Expected: all previously passing tests still pass (2 pre-existing failures in `test_state_persistence.py` are unrelated to this change).

- [ ] **Step 8: Commit**

```bash
git add src/api/models.py src/api/endpoints/groceries.py src/api/main.py tests/test_api/test_groceries.py
git commit -m "feat: add POST /groceries endpoint for NL grocery parsing"
```

---

### Task 2: Frontend project scaffold

**Files:**
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/tsconfig.node.json`
- Create: `web/vite.config.ts`
- Create: `web/tailwind.config.ts`
- Create: `web/postcss.config.ts`
- Create: `web/index.html`
- Create: `web/.env.example`
- Create: `web/src/index.css`
- Create: `web/src/test/setup.ts`
- Create: `web/src/test/server.ts`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: nothing
- Produces: `npm run dev`, `npm run test` commands; MSW `server` export from `web/src/test/server.ts` (used by all feature tests)

- [ ] **Step 1: Add frontend entries to root `.gitignore`**

Append to `.gitignore`:
```
# --- Frontend ---
web/node_modules/
web/dist/
web/.env
```

- [ ] **Step 2: Create `web/package.json`**

```json
{
  "name": "meal-planner-web",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:run": "vitest run"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.62.7",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.27.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.1.0",
    "@testing-library/user-event": "^14.5.2",
    "@types/react": "^18.3.18",
    "@types/react-dom": "^18.3.5",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "jsdom": "^25.0.1",
    "msw": "^2.7.0",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "typescript": "^5.7.2",
    "vite": "^6.0.0",
    "vitest": "^2.1.8"
  }
}
```

- [ ] **Step 3: Create `web/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 4: Create `web/tsconfig.node.json`**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts", "tailwind.config.ts", "postcss.config.ts"]
}
```

- [ ] **Step 5: Create `web/vite.config.ts`**

```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
```

- [ ] **Step 6: Create `web/tailwind.config.ts`**

```typescript
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: { extend: {} },
  plugins: [],
} satisfies Config
```

- [ ] **Step 7: Create `web/postcss.config.ts`**

```typescript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 8: Create `web/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Meal Planner</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 9: Create `web/.env.example`**

```
VITE_API_KEY=dev-key-change-in-production
```

- [ ] **Step 10: Create `web/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 11: Create `web/src/test/server.ts`**

```typescript
import { setupServer } from 'msw/node'

export const server = setupServer()
```

- [ ] **Step 12: Create `web/src/test/setup.ts`**

```typescript
import '@testing-library/jest-dom'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { server } from './server'

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

- [ ] **Step 13: Install dependencies**

```bash
cd web && npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 14: Verify test runner starts with zero tests**

```bash
cd web && npm run test:run
```

Expected: `0 tests passed` (no test files yet) — not an error.

- [ ] **Step 15: Commit**

```bash
git add .gitignore web/
git commit -m "feat: scaffold React + Vite + TS frontend with Tailwind and MSW test setup"
```

---

### Task 3: API types and client

**Files:**
- Create: `web/src/api/types.ts`
- Create: `web/src/api/client.ts`
- Create: `web/src/api/client.test.ts`

**Interfaces:**
- Consumes: nothing from prior tasks
- Produces: `api` object, `ApiError` class (used by all feature hooks and components); all TypeScript types (used by all feature files)

- [ ] **Step 1: Write the failing tests**

Create `web/src/api/client.test.ts`:

```typescript
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { api, ApiError } from './client'

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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd web && npm run test:run -- --reporter=verbose
```

Expected: errors — `./client` module not found.

- [ ] **Step 3: Create `web/src/api/types.ts`**

```typescript
export interface MealItem {
  name: string
  calories: number
  macros: { protein: number; carbs: number; fat: number }
  ingredients: string[]
}

export interface DayPlan {
  day: string
  meals: MealItem[]
  total_calories: number
  total_protein: number
  total_carbs: number
}

export interface GroceryListItem {
  item: string
  quantity: number
  unit: string
  category: string
}

export interface MealPlanRequest {
  days?: string[]
  preferences?: string
}

export interface MealPlanResponse {
  plan_id: string
  plan: DayPlan[]
  grocery_list: GroceryListItem[]
  status: string
  message?: string
}

export interface MealResponse {
  name: string
  version: string
  category: string
  macros: { calories: number; protein: number; carbs: number; fat: number }
  ingredients: string[]
  instructions: string[]
  tags: string[]
}

export interface AddMealRequest {
  name: string
  ingredients: string[]
  macros: { calories: number; protein: number; carbs: number; fat: number }
  instructions: string[]
  category: string
  tags: string[]
}

export interface AddMealResponse {
  success: boolean
  meal_name: string
  newly_added: string[]
  category: string
  message: string
}

export interface SearchParams {
  category?: string
  min_cal?: number
  max_cal?: number
  min_prot?: number
  max_prot?: number
  min_carb?: number
  max_carb?: number
  min_fat?: number
  max_fat?: number
  ingredient?: string
  tag?: string
  search_term?: string
}

export interface GroceryParseResult {
  raw_phrase: string
  standardized_item: string
  quantity: number
  unit: string
  match: string
  confidence_score: number
  confidence_level: string
  status: 'auto' | 'review' | 'manual'
}

export interface GroceriesResponse {
  items: GroceryParseResult[]
  saved_count: number
  review_count: number
}

export interface AppState {
  current_day: string
  plan_id: string
  plan: DayPlan[]
  grocery_list: GroceryListItem[]
  missing_macros: string[]
  grocery_inventory: Record<string, unknown>[]
  unmatched_groceries: Record<string, unknown>[]
  inventory_usage: { used: string[]; unused: string[]; supplemental: string[] }
}
```

- [ ] **Step 4: Create `web/src/api/client.ts`**

```typescript
import type {
  AddMealRequest,
  AddMealResponse,
  AppState,
  GroceriesResponse,
  MealPlanRequest,
  MealPlanResponse,
  MealResponse,
  SearchParams,
} from './types'

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
  },
  groceries: {
    add: (text: string) =>
      request<GroceriesResponse>('/groceries/', {
        method: 'POST',
        body: JSON.stringify({ text }),
      }),
  },
}
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd web && npm run test:run
```

Expected: 4 passed, 0 failed.

- [ ] **Step 6: Commit**

```bash
git add web/src/api/
git commit -m "feat: add typed API client and TypeScript types"
```

---

### Task 4: Shared UI components

**Files:**
- Create: `web/src/components/Spinner.tsx`
- Create: `web/src/components/ErrorBanner.tsx`
- Create: `web/src/components/Card.tsx`
- Create: `web/src/components/Table.tsx`

**Interfaces:**
- Consumes: nothing from prior tasks
- Produces: `<Spinner />`, `<ErrorBanner message={string} />`, `<Card>children</Card>`, `<Table columns={Column[]} rows={Row[]} />` (used by all feature pages)

- [ ] **Step 1: Create `web/src/components/Spinner.tsx`**

```tsx
export function Spinner() {
  return (
    <div className="flex justify-center py-8">
      <div className="w-8 h-8 border-4 border-green-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
```

- [ ] **Step 2: Create `web/src/components/ErrorBanner.tsx`**

```tsx
interface ErrorBannerProps {
  message: string
}

export function ErrorBanner({ message }: ErrorBannerProps) {
  return (
    <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700 text-sm">
      {message}
    </div>
  )
}
```

- [ ] **Step 3: Create `web/src/components/Card.tsx`**

```tsx
interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${className}`}>
      {children}
    </div>
  )
}
```

- [ ] **Step 4: Create `web/src/components/Table.tsx`**

```tsx
export interface Column {
  key: string
  header: string
  render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode
}

interface TableProps {
  columns: Column[]
  rows: Record<string, unknown>[]
}

export function Table({ columns, rows }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100">
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-3 py-2 text-left font-semibold text-gray-700"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-gray-200 hover:bg-gray-50">
              {columns.map((col) => (
                <td key={col.key} className="px-3 py-2 text-gray-700">
                  {col.render
                    ? col.render(row[col.key], row)
                    : String(row[col.key] ?? '')}
                </td>
              ))}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td
                colSpan={columns.length}
                className="px-3 py-4 text-center text-gray-400 text-sm"
              >
                No data
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
```

- [ ] **Step 5: Verify TypeScript compiles**

```bash
cd web && npx tsc --noEmit
```

Expected: no errors (or only errors about missing feature files that don't exist yet — those will be resolved in later tasks).

- [ ] **Step 6: Commit**

```bash
git add web/src/components/
git commit -m "feat: add shared UI components (Spinner, ErrorBanner, Card, Table)"
```

---

### Task 5: App shell

**Files:**
- Create: `web/src/App.tsx`
- Create: `web/src/main.tsx`

**Interfaces:**
- Consumes: `<Spinner />`, `<ErrorBanner />` from Task 4; `QueryClient` from `@tanstack/react-query`; all feature page components (stubs must exist before this compiles — create stub files if features aren't done yet)
- Produces: full routed app at `http://localhost:5173/`; navigates `/` → `/plan` automatically

- [ ] **Step 1: Create stub feature page files** (if Tasks 6–9 are not yet done)

If `web/src/features/` doesn't have the feature files yet, create minimal stubs so the shell compiles:

`web/src/features/plan/PlanPage.tsx`:
```tsx
export function PlanPage() { return <div>Plan</div> }
```

`web/src/features/meals/MealsPage.tsx`:
```tsx
export function MealsPage() { return <div>Meals</div> }
```

`web/src/features/meals/MealDetailPage.tsx`:
```tsx
export function MealDetailPage() { return <div>Meal Detail</div> }
```

`web/src/features/groceries/GroceriesPage.tsx`:
```tsx
export function GroceriesPage() { return <div>Groceries</div> }
```

`web/src/features/state/StatePage.tsx`:
```tsx
export function StatePage() { return <div>State</div> }
```

- [ ] **Step 2: Create `web/src/App.tsx`**

```tsx
import { NavLink, Outlet } from 'react-router-dom'

export function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-3 flex gap-6 text-sm font-medium">
          <NavLink
            to="/plan"
            className={({ isActive }) =>
              isActive ? 'text-green-600' : 'text-gray-600 hover:text-green-600'
            }
          >
            Plan
          </NavLink>
          <NavLink
            to="/meals"
            className={({ isActive }) =>
              isActive ? 'text-green-600' : 'text-gray-600 hover:text-green-600'
            }
          >
            Meals
          </NavLink>
          <NavLink
            to="/groceries"
            className={({ isActive }) =>
              isActive ? 'text-green-600' : 'text-gray-600 hover:text-green-600'
            }
          >
            Groceries
          </NavLink>
          <NavLink
            to="/state"
            className={({ isActive }) =>
              isActive ? 'text-green-600' : 'text-gray-600 hover:text-green-600'
            }
          >
            State
          </NavLink>
        </div>
      </nav>
      <main className="max-w-5xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  )
}
```

- [ ] **Step 3: Create `web/src/main.tsx`**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { App } from './App'
import { PlanPage } from './features/plan/PlanPage'
import { MealsPage } from './features/meals/MealsPage'
import { MealDetailPage } from './features/meals/MealDetailPage'
import { GroceriesPage } from './features/groceries/GroceriesPage'
import { StatePage } from './features/state/StatePage'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<App />}>
            <Route index element={<Navigate to="/plan" replace />} />
            <Route path="plan" element={<PlanPage />} />
            <Route path="meals" element={<MealsPage />} />
            <Route path="meals/:name" element={<MealDetailPage />} />
            <Route path="groceries" element={<GroceriesPage />} />
            <Route path="state" element={<StatePage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
)
```

- [ ] **Step 4: Create `web/.env` from example**

```bash
cd web && cp .env.example .env
```

- [ ] **Step 5: Start the dev server and verify navigation**

```bash
cd web && npm run dev
```

Open `http://localhost:5173/` — should redirect to `/plan` and show the nav with Plan / Meals / Groceries / State links. Each link should navigate without a full page reload.

- [ ] **Step 6: Commit**

```bash
git add web/src/App.tsx web/src/main.tsx web/src/features/ web/.env.example
git commit -m "feat: add app shell with nav and React Router routes"
```

---

### Task 6: Plan feature

**Files:**
- Create: `web/src/features/plan/hooks.ts`
- Create: `web/src/features/plan/PlanPage.tsx`
- Create: `web/src/features/plan/PlanPage.test.tsx`

**Interfaces:**
- Consumes: `api.plan.get`, `api.plan.generate` from Task 3; `Spinner`, `ErrorBanner`, `Card` from Task 4; `ApiError` from Task 3
- Produces: `usePlan()`, `useGeneratePlan()` hooks; `/plan` page with day selector and meal cards linking to `/meals/:name`

- [ ] **Step 1: Write failing tests**

Create `web/src/features/plan/PlanPage.test.tsx`:

```tsx
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd web && npm run test:run -- src/features/plan/PlanPage.test.tsx
```

Expected: errors — `PlanPage` module not found.

- [ ] **Step 3: Create `web/src/features/plan/hooks.ts`**

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { MealPlanRequest } from '../../api/types'

export function usePlan() {
  return useQuery({ queryKey: ['plan'], queryFn: api.plan.get })
}

export function useGeneratePlan() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: MealPlanRequest) => api.plan.generate(req),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['plan'] }),
  })
}
```

- [ ] **Step 4: Create `web/src/features/plan/PlanPage.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../../api/client'
import { Card } from '../../components/Card'
import { ErrorBanner } from '../../components/ErrorBanner'
import { Spinner } from '../../components/Spinner'
import { usePlan, useGeneratePlan } from './hooks'

export function PlanPage() {
  const { data: planData, isLoading, isError, error } = usePlan()
  const generate = useGeneratePlan()
  const [selectedDay, setSelectedDay] = useState('')
  const [preferences, setPreferences] = useState('')

  const days = planData?.plan ?? []

  useEffect(() => {
    if (days.length > 0 && !selectedDay) {
      setSelectedDay(days[0].day)
    }
  }, [days, selectedDay])

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner
        message={error instanceof ApiError ? error.message : 'Failed to load plan'}
      />
    )

  const currentDayPlan = days.find((d) => d.day === selectedDay) ?? days[0]

  return (
    <div>
      <div className="flex gap-3 mb-6">
        <input
          type="text"
          placeholder="Preferences (optional)"
          value={preferences}
          onChange={(e) => setPreferences(e.target.value)}
          className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        <button
          onClick={() => generate.mutate({ preferences: preferences || undefined })}
          disabled={generate.isPending}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-sm font-medium"
        >
          {generate.isPending ? 'Generating…' : 'Generate Plan'}
        </button>
      </div>

      {generate.isError && <ErrorBanner message="Failed to generate plan" />}

      {days.length === 0 ? (
        <p className="text-gray-500 text-sm">No plan yet — click Generate Plan.</p>
      ) : (
        <>
          <div className="flex gap-2 mb-4 flex-wrap">
            {days.map((d) => (
              <button
                key={d.day}
                onClick={() => setSelectedDay(d.day)}
                className={`px-3 py-1 rounded text-sm font-medium ${
                  selectedDay === d.day
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {d.day}
              </button>
            ))}
          </div>

          {currentDayPlan && (
            <div>
              <p className="text-sm text-gray-500 mb-3">
                {currentDayPlan.total_calories} kcal · {currentDayPlan.total_protein}g protein ·{' '}
                {currentDayPlan.total_carbs}g carbs
              </p>
              <div className="grid gap-3">
                {currentDayPlan.meals.map((meal) => (
                  <Card key={meal.name}>
                    <Link
                      to={`/meals/${encodeURIComponent(meal.name)}`}
                      state={{ planMeal: meal }}
                      className="font-semibold hover:text-green-600"
                    >
                      {meal.name}
                    </Link>
                    <p className="text-sm text-gray-500 mt-1">
                      {meal.calories} kcal · {meal.macros.protein}g protein ·{' '}
                      {meal.macros.carbs}g carbs · {meal.macros.fat}g fat
                    </p>
                    {meal.ingredients.length > 0 && (
                      <p className="text-sm text-gray-600 mt-2">
                        {meal.ingredients.join(', ')}
                      </p>
                    )}
                  </Card>
                ))}
              </div>

              {(planData?.grocery_list.length ?? 0) > 0 && (
                <p className="mt-4 text-sm">
                  <Link to="/groceries" className="text-green-600 hover:underline">
                    View grocery list ({planData!.grocery_list.length} items) →
                  </Link>
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd web && npm run test:run -- src/features/plan/PlanPage.test.tsx
```

Expected: 6 passed, 0 failed.

- [ ] **Step 6: Commit**

```bash
git add web/src/features/plan/
git commit -m "feat: add plan feature page with day selector and meal card links"
```

---

### Task 7: Meals feature

**Files:**
- Create: `web/src/features/meals/hooks.ts`
- Create: `web/src/features/meals/MealsPage.tsx`
- Create: `web/src/features/meals/MealDetailPage.tsx`
- Create: `web/src/features/meals/MealsPage.test.tsx`
- Create: `web/src/features/meals/MealDetailPage.test.tsx`

**Interfaces:**
- Consumes: `api.meals.*` from Task 3; `Spinner`, `ErrorBanner`, `Card`, `Table` from Task 4; `ApiError` from Task 3
- Produces: `useMeals()`, `useSearchMeals(params)`, `useAddMeal()` hooks; `/meals` list+search+add page; `/meals/:name` detail page with saved-meal and plan-meal fallback

- [ ] **Step 1: Write failing tests**

Create `web/src/features/meals/MealsPage.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { MealsPage } from './MealsPage'

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const MEALS = [
  {
    name: 'Chicken Bowl',
    version: '2024-01-01',
    category: 'Dinner',
    macros: { calories: 500, protein: 35, carbs: 40, fat: 12 },
    ingredients: ['Chicken', 'Rice'],
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
})
```

Create `web/src/features/meals/MealDetailPage.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { MealDetailPage } from './MealDetailPage'
import type { MealItem } from '../../api/types'

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

const SAVED_MEAL = {
  name: 'Chicken Bowl',
  version: '2024-01-01',
  category: 'Dinner',
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd web && npm run test:run -- src/features/meals/
```

Expected: errors — modules not found.

- [ ] **Step 3: Create `web/src/features/meals/hooks.ts`**

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { AddMealRequest, SearchParams } from '../../api/types'

export function useMeals() {
  return useQuery({ queryKey: ['meals'], queryFn: () => api.meals.list() })
}

export function useSearchMeals(params: SearchParams) {
  return useQuery({
    queryKey: ['meals', 'search', params],
    queryFn: () => api.meals.search(params),
  })
}

export function useAddMeal() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: AddMealRequest) => api.meals.add(req),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['meals'] }),
  })
}
```

- [ ] **Step 4: Create `web/src/features/meals/MealsPage.tsx`**

```tsx
import { useState } from 'react'
import { ErrorBanner } from '../../components/ErrorBanner'
import { Spinner } from '../../components/Spinner'
import { Table } from '../../components/Table'
import type { AddMealRequest, SearchParams } from '../../api/types'
import { ApiError } from '../../api/client'
import { useSearchMeals, useAddMeal } from './hooks'

export function MealsPage() {
  const [filters, setFilters] = useState<SearchParams>({})
  const [searchInput, setSearchInput] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const { data: meals, isLoading, isError, error } = useSearchMeals(filters)
  const addMeal = useAddMeal()

  const [form, setForm] = useState({
    name: '', ingredients: '', calories: '', protein: '', carbs: '', fat: '',
    instructions: '', category: 'Dinner', tags: '',
  })

  const handleSearch = () => {
    setFilters(searchInput.trim() ? { search_term: searchInput.trim() } : {})
  }

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const req: AddMealRequest = {
      name: form.name,
      ingredients: form.ingredients.split(',').map((s) => s.trim()).filter(Boolean),
      macros: {
        calories: parseInt(form.calories) || 0,
        protein: parseInt(form.protein) || 0,
        carbs: parseInt(form.carbs) || 0,
        fat: parseInt(form.fat) || 0,
      },
      instructions: form.instructions.split(';').map((s) => s.trim()).filter(Boolean),
      category: form.category,
      tags: form.tags.split(',').map((s) => s.trim()).filter(Boolean),
    }
    addMeal.mutate(req, {
      onSuccess: () => {
        setShowAdd(false)
        setForm({ name: '', ingredients: '', calories: '', protein: '', carbs: '', fat: '', instructions: '', category: 'Dinner', tags: '' })
      },
    })
  }

  if (isLoading) return <Spinner />
  if (isError)
    return <ErrorBanner message={error instanceof ApiError ? error.message : 'Failed to load meals'} />

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          placeholder="Search meals…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        <button
          onClick={handleSearch}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm font-medium"
        >
          Search
        </button>
        <button
          onClick={() => setShowAdd((v) => !v)}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm font-medium"
        >
          Add Meal
        </button>
      </div>

      {showAdd && (
        <form onSubmit={handleAddSubmit} className="mb-6 bg-white border border-gray-200 rounded-lg p-4 space-y-3">
          <h2 className="font-semibold text-gray-800">New Meal</h2>
          <div>
            <label htmlFor="meal-name" className="block text-sm text-gray-600 mb-1">Meal name</label>
            <input id="meal-name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Ingredients (comma-separated)</label>
            <input value={form.ingredients} onChange={(e) => setForm({ ...form, ingredients: e.target.value })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>
          <div className="grid grid-cols-4 gap-2">
            {(['calories', 'protein', 'carbs', 'fat'] as const).map((macro) => (
              <div key={macro}>
                <label className="block text-xs text-gray-500 mb-1 capitalize">{macro}</label>
                <input type="number" min="0" value={form[macro]} onChange={(e) => setForm({ ...form, [macro]: e.target.value })} className="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
              </div>
            ))}
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Instructions (semicolon-separated)</label>
            <textarea value={form.instructions} onChange={(e) => setForm({ ...form, instructions: e.target.value })} rows={2} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Category</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                {['Breakfast', 'Lunch', 'Dinner', 'Snack'].map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Tags (comma-separated)</label>
              <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={addMeal.isPending} className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 text-sm disabled:opacity-50">
              {addMeal.isPending ? 'Saving…' : 'Save Meal'}
            </button>
            <button type="button" onClick={() => setShowAdd(false)} className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm">
              Cancel
            </button>
          </div>
          {addMeal.isError && <ErrorBanner message="Failed to add meal" />}
        </form>
      )}

      <Table
        columns={[
          { key: 'name', header: 'Name' },
          { key: 'category', header: 'Category' },
          { key: 'macros', header: 'Calories', render: (v) => (v as { calories: number }).calories },
          { key: 'macros', header: 'Protein', render: (v) => `${(v as { protein: number }).protein}g` },
          { key: 'macros', header: 'Carbs', render: (v) => `${(v as { carbs: number }).carbs}g` },
          { key: 'macros', header: 'Fat', render: (v) => `${(v as { fat: number }).fat}g` },
        ]}
        rows={(meals ?? []) as unknown as Record<string, unknown>[]}
      />
    </div>
  )
}
```

- [ ] **Step 5: Create `web/src/features/meals/MealDetailPage.tsx`**

```tsx
import { useLocation, useParams } from 'react-router-dom'
import { ApiError } from '../../api/client'
import { Card } from '../../components/Card'
import { ErrorBanner } from '../../components/ErrorBanner'
import { Spinner } from '../../components/Spinner'
import type { MealItem } from '../../api/types'
import { useMeals } from './hooks'

export function MealDetailPage() {
  const { name } = useParams<{ name: string }>()
  const location = useLocation()
  const decodedName = decodeURIComponent(name ?? '')
  const { data: meals, isLoading, isError, error } = useMeals()

  const planMeal = (location.state as { planMeal?: MealItem } | null)?.planMeal
  const savedMeal = meals?.find((m) => m.name === decodedName)

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner
        message={error instanceof ApiError ? error.message : 'Failed to load meals'}
      />
    )

  if (savedMeal) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-1">{savedMeal.name}</h1>
        <p className="text-sm text-gray-500 mb-1">{savedMeal.category}</p>
        <p className="text-sm text-gray-600 mb-4">
          {savedMeal.macros.calories} kcal · {savedMeal.macros.protein}g protein ·{' '}
          {savedMeal.macros.carbs}g carbs · {savedMeal.macros.fat}g fat
        </p>
        <div className="grid md:grid-cols-2 gap-4">
          <Card>
            <h2 className="font-semibold mb-2">Ingredients</h2>
            <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
              {savedMeal.ingredients.map((ing) => <li key={ing}>{ing}</li>)}
            </ul>
          </Card>
          <Card>
            <h2 className="font-semibold mb-2">Instructions</h2>
            <ol className="list-decimal pl-5 text-sm text-gray-700 space-y-1">
              {savedMeal.instructions.map((step, i) => <li key={i}>{step}</li>)}
            </ol>
          </Card>
        </div>
        {savedMeal.tags.length > 0 && (
          <div className="mt-4 flex gap-2 flex-wrap">
            {savedMeal.tags.map((tag) => (
              <span key={tag} className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    )
  }

  if (planMeal) {
    return (
      <div>
        <div className="mb-3 rounded bg-amber-50 border border-amber-200 p-3 text-sm text-amber-700">
          This meal is not in your saved library.
        </div>
        <h1 className="text-2xl font-bold mb-2">{planMeal.name}</h1>
        <p className="text-sm text-gray-600 mb-4">
          {planMeal.calories} kcal · {planMeal.macros.protein}g protein ·{' '}
          {planMeal.macros.carbs}g carbs · {planMeal.macros.fat}g fat
        </p>
        {planMeal.ingredients.length > 0 && (
          <Card>
            <h2 className="font-semibold mb-2">Ingredients</h2>
            <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
              {planMeal.ingredients.map((ing) => <li key={ing}>{ing}</li>)}
            </ul>
          </Card>
        )}
      </div>
    )
  }

  return <p className="text-gray-500">Meal "{decodedName}" not found.</p>
}
```

- [ ] **Step 6: Run tests to confirm they pass**

```bash
cd web && npm run test:run -- src/features/meals/
```

Expected: 6 passed (3 MealsPage + 3 MealDetailPage), 0 failed.

- [ ] **Step 7: Commit**

```bash
git add web/src/features/meals/
git commit -m "feat: add meals list/search/add page and meal detail page with plan fallback"
```

---

### Task 8: State feature

**Files:**
- Create: `web/src/features/state/hooks.ts`
- Create: `web/src/features/state/StatePage.tsx`
- Create: `web/src/features/state/StatePage.test.tsx`

**Interfaces:**
- Consumes: `api.state.get` from Task 3; `Spinner`, `ErrorBanner`, `Table` from Task 4; `ApiError` from Task 3
- Produces: `useAppState()` hook (also imported by Task 9 Groceries feature); `/state` read-only view

- [ ] **Step 1: Write failing test**

Create `web/src/features/state/StatePage.test.tsx`:

```tsx
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
  unmatched_groceries: [{ raw_phrase: 'saffron', standardized_item: 'saffron', source: 'specialty' }],
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
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
cd web && npm run test:run -- src/features/state/StatePage.test.tsx
```

Expected: errors — modules not found.

- [ ] **Step 3: Create `web/src/features/state/hooks.ts`**

```typescript
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'

export function useAppState() {
  return useQuery({ queryKey: ['state'], queryFn: api.state.get })
}
```

- [ ] **Step 4: Create `web/src/features/state/StatePage.tsx`**

```tsx
import { ApiError } from '../../api/client'
import { ErrorBanner } from '../../components/ErrorBanner'
import { Spinner } from '../../components/Spinner'
import { Table } from '../../components/Table'
import { useAppState } from './hooks'

export function StatePage() {
  const { data: state, isLoading, isError, error } = useAppState()

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner
        message={error instanceof ApiError ? error.message : 'Failed to load state'}
      />
    )
  if (!state) return null

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-lg font-semibold mb-3">Current State</h2>
        <dl className="grid grid-cols-2 gap-y-2 gap-x-4 text-sm max-w-sm">
          <dt className="text-gray-500">Current Day</dt>
          <dd className="font-medium">{state.current_day}</dd>
          <dt className="text-gray-500">Plan ID</dt>
          <dd className="font-mono text-xs truncate">{state.plan_id}</dd>
        </dl>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Inventory Usage</h2>
        <div className="grid grid-cols-3 gap-4 text-sm">
          {(
            [
              { label: 'Used', key: 'used' as const, color: 'text-green-600' },
              { label: 'Unused', key: 'unused' as const, color: 'text-gray-500' },
              { label: 'Supplemental', key: 'supplemental' as const, color: 'text-blue-600' },
            ] as const
          ).map(({ label, key, color }) => (
            <div key={key}>
              <h3 className={`font-medium mb-1 ${color}`}>
                {label} ({state.inventory_usage[key].length})
              </h3>
              <ul className="space-y-0.5 text-gray-700">
                {state.inventory_usage[key].map((item) => (
                  <li key={item}>{item}</li>
                ))}
                {state.inventory_usage[key].length === 0 && (
                  <li className="text-gray-400">—</li>
                )}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {state.unmatched_groceries.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Unmatched Groceries</h2>
          <Table
            columns={[
              { key: 'raw_phrase', header: 'Raw' },
              { key: 'standardized_item', header: 'Standardized' },
              { key: 'source', header: 'Source' },
            ]}
            rows={state.unmatched_groceries}
          />
        </section>
      )}

      {state.missing_macros.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Missing Macros</h2>
          <ul className="text-sm text-gray-700 list-disc pl-5 space-y-1">
            {state.missing_macros.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd web && npm run test:run -- src/features/state/StatePage.test.tsx
```

Expected: 3 passed, 0 failed.

- [ ] **Step 6: Commit**

```bash
git add web/src/features/state/
git commit -m "feat: add state feature page with inventory usage and unmatched groceries"
```

---

### Task 9: Groceries feature

**Files:**
- Create: `web/src/features/groceries/hooks.ts`
- Create: `web/src/features/groceries/GroceriesPage.tsx`
- Create: `web/src/features/groceries/GroceriesPage.test.tsx`

**Interfaces:**
- Consumes: `api.groceries.add`, `api.state.get` from Task 3; `useAppState()` from Task 8; `Spinner`, `ErrorBanner`, `Table` from Task 4; `ApiError` from Task 3
- Produces: `useAddGroceries()` hook; `/groceries` page with NL add box, parse result table, grocery list, and inventory

- [ ] **Step 1: Write failing tests**

Create `web/src/features/groceries/GroceriesPage.test.tsx`:

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { GroceriesPage } from './GroceriesPage'

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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd web && npm run test:run -- src/features/groceries/GroceriesPage.test.tsx
```

Expected: errors — modules not found.

- [ ] **Step 3: Create `web/src/features/groceries/hooks.ts`**

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'

export function useAddGroceries() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (text: string) => api.groceries.add(text),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['state'] }),
  })
}
```

- [ ] **Step 4: Create `web/src/features/groceries/GroceriesPage.tsx`**

```tsx
import { useState } from 'react'
import { ApiError } from '../../api/client'
import { ErrorBanner } from '../../components/ErrorBanner'
import { Spinner } from '../../components/Spinner'
import { Table } from '../../components/Table'
import { useAppState } from '../state/hooks'
import type { GroceryParseResult } from '../../api/types'
import { useAddGroceries } from './hooks'

export function GroceriesPage() {
  const [text, setText] = useState('')
  const { data: state, isLoading, isError, error } = useAppState()
  const addGroceries = useAddGroceries()

  const handleAdd = () => {
    if (!text.trim()) return
    addGroceries.mutate(text, { onSuccess: () => setText('') })
  }

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner
        message={error instanceof ApiError ? error.message : 'Failed to load state'}
      />
    )

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-lg font-semibold mb-3">Add Groceries</h2>
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
            placeholder="I got two pounds of chicken thighs, spinach…"
            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            onClick={handleAdd}
            disabled={addGroceries.isPending || !text.trim()}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-sm font-medium"
          >
            {addGroceries.isPending ? 'Parsing…' : 'Add'}
          </button>
        </div>
        {addGroceries.isError && <ErrorBanner message="Failed to parse groceries" />}
        {addGroceries.data && <ParseResultTable result={addGroceries.data.items} savedCount={addGroceries.data.saved_count} reviewCount={addGroceries.data.review_count} />}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Grocery List</h2>
        {(state?.grocery_list.length ?? 0) === 0 ? (
          <p className="text-sm text-gray-400">No grocery list yet.</p>
        ) : (
          <Table
            columns={[
              { key: 'item', header: 'Item' },
              { key: 'quantity', header: 'Qty' },
              { key: 'unit', header: 'Unit' },
              { key: 'category', header: 'Category' },
            ]}
            rows={state!.grocery_list as unknown as Record<string, unknown>[]}
          />
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">Inventory</h2>
        {(state?.grocery_inventory.length ?? 0) === 0 ? (
          <p className="text-sm text-gray-400">No inventory yet.</p>
        ) : (
          <Table
            columns={[
              { key: 'standardized_item', header: 'Item' },
              { key: 'quantity', header: 'Qty' },
              { key: 'unit', header: 'Unit' },
            ]}
            rows={state!.grocery_inventory}
          />
        )}
      </section>
    </div>
  )
}

function ParseResultTable({
  result,
  savedCount,
  reviewCount,
}: {
  result: GroceryParseResult[]
  savedCount: number
  reviewCount: number
}) {
  return (
    <div>
      <p className="text-sm text-gray-600 mb-2">
        Saved: {savedCount} · Review/Manual: {reviewCount}
      </p>
      <Table
        columns={[
          { key: 'raw_phrase', header: 'Raw' },
          { key: 'standardized_item', header: 'Standardized' },
          { key: 'quantity', header: 'Qty' },
          { key: 'unit', header: 'Unit' },
          { key: 'match', header: 'Match' },
          {
            key: 'confidence_score',
            header: 'Confidence',
            render: (v) => Number(v).toFixed(2),
          },
          { key: 'status', header: 'Status' },
        ]}
        rows={result as unknown as Record<string, unknown>[]}
      />
    </div>
  )
}
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
cd web && npm run test:run -- src/features/groceries/GroceriesPage.test.tsx
```

Expected: 4 passed, 0 failed.

- [ ] **Step 6: Run full frontend test suite**

```bash
cd web && npm run test:run
```

Expected: all tests pass (client + plan + meals + state + groceries).

- [ ] **Step 7: Commit**

```bash
git add web/src/features/groceries/
git commit -m "feat: add groceries page with NL add, parse result table, grocery list, and inventory"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| POST /groceries endpoint reusing tools/ layer | Task 1 |
| `GroceriesRequest`, `GroceriesResponse` Pydantic models | Task 1 |
| Pytest for new endpoint with mocked tools | Task 1 |
| React + Vite + TS + Tailwind scaffold | Task 2 |
| MSW + Vitest test setup | Task 2 |
| Typed `api/client.ts` with `ApiError`, 401 → friendly message | Task 3 |
| TypeScript types mirroring all Pydantic models | Task 3 |
| Shared Spinner, ErrorBanner, Card, Table | Task 4 |
| App shell with nav and routes | Task 5 |
| `/plan` page — generate button, day selector, meal cards | Task 6 |
| Meal cards link to `/meals/:name` via `<Link state={planMeal}>` | Task 6 |
| Grocery list link from plan page | Task 6 |
| `/meals` page — search/filter, add-meal form, list table | Task 7 |
| `/meals/:name` detail — saved meal or plan-meal fallback | Task 7 |
| "Not in saved library" notice when no saved meal matches | Task 7 |
| `/state` page — current day, plan id, inventory usage, unmatched | Task 8 |
| `useAppState()` hook shared by state + groceries features | Task 8 |
| `/groceries` page — NL add box, parse result table, list, inventory | Task 9 |
| State query invalidated after grocery add | Task 9 |
| Query keys consistent: `['plan']`, `['meals']`, `['state']` | Tasks 3, 6, 7, 8, 9 |

**No placeholders or TBDs found.**

**Type consistency:** All types flow from `web/src/api/types.ts` defined in Task 3. `useAppState()` defined in Task 8 is imported by Task 9 at `../state/hooks`. Query key `['state']` used in both Task 8 (`useAppState`) and Task 9 (`useAddGroceries` invalidation).
