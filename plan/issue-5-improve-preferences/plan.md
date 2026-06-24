# Preferences UI Implementation Plan

GitHub Issue: https://github.com/evanmei87/meal-planner/issues/5

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist meal-plan preferences in app state so they survive page reloads, pre-fill the Plan page input, and are viewable/editable on the State page with a Regenerate Plan button.

**Architecture:** `preferences` is added as an optional string field to `state.json`, read/written through the existing `GET /state/` and `PUT /state/` endpoints. The Plan page pre-fills from state on mount and persists on generate. The State page gets a new Preferences section with Save and Regenerate Plan controls.

**Tech Stack:** Python 3 / FastAPI / Pydantic (backend); React / TypeScript / TanStack Query / MSW / Vitest (frontend).

## Global Constraints

- Branch: `feat/5-preferences-enhance`
- All new behaviour must be covered by tests before implementation (TDD).
- Backend tests: `pytest tests/test_api/test_state.py -v`
- Frontend tests: run from `web/` → `npm test -- --run`
- Do not reformat or restructure code outside the files listed.
- Follow existing code style exactly (Tailwind classes, naming, import order).

---

## File Map

| File | Change |
|------|--------|
| `src/api/models.py` | Add `preferences` field to `StateResponse` and `UpdateStateRequest` |
| `src/api/endpoints/state.py` | Read/write `preferences` in GET and PUT handlers; update docstrings |
| `tests/test_api/test_state.py` | Two new tests covering preferences round-trip |
| `web/src/api/types.ts` | Add `preferences?: string` to `AppState` |
| `web/src/api/client.ts` | Add `api.state.update()` method |
| `web/src/features/state/hooks.ts` | Add `useUpdateState` mutation |
| `web/src/features/plan/PlanPage.tsx` | Placeholder text, pre-fill from state, persist on generate |
| `web/src/features/plan/PlanPage.test.tsx` | `beforeEach` default state mock; two new tests |
| `web/src/features/state/StatePage.tsx` | Preferences section with Save and Regenerate Plan |
| `web/src/features/state/StatePage.test.tsx` | Four new tests |

---

## Task 1: Backend — add `preferences` to state models and endpoints

**Files:**
- Modify: `src/api/models.py`
- Modify: `src/api/endpoints/state.py`
- Modify (tests): `tests/test_api/test_state.py`

**Interfaces:**
- Produces: `StateResponse.preferences: Optional[str]`, `UpdateStateRequest.preferences: Optional[str]`
- Produces: `GET /state/` returns `preferences` field; `PUT /state/` accepts and persists `preferences`

---

- [ ] **Step 1: Write failing test — GET /state/ returns preferences**

Add these two tests at the bottom of `tests/test_api/test_state.py`:

```python
def test_get_state_returns_preferences(client, api_key_headers, temp_state_file):
    """GET /state/ includes the preferences field when present in state."""
    state_data = {
        'current_day': 'Monday',
        'plan_id': 'test-plan-123',
        'plan': [],
        'grocery_list': [],
        'missing_macros': [],
        'preferences': 'high protein, no red meat',
    }
    Path(temp_state_file).write_text(json.dumps(state_data))

    with patch('src.api.endpoints.state.STATE_PATH', temp_state_file):
        response = client.get('/state/', headers=api_key_headers)

    assert response.status_code == 200
    assert response.json()['preferences'] == 'high protein, no red meat'


def test_update_state_persists_preferences(client, api_key_headers, temp_state_file):
    """PUT /state/ with preferences merges it into state and returns it."""
    initial_state = {
        'current_day': 'Monday',
        'plan_id': 'test-plan-123',
        'plan': [],
        'grocery_list': [],
        'missing_macros': [],
    }
    Path(temp_state_file).write_text(json.dumps(initial_state))

    with patch('src.api.endpoints.state.STATE_PATH', temp_state_file):
        with patch('src.api.endpoints.state.update_state') as mock_update:
            mock_update.return_value = True
            response = client.put(
                '/state/',
                json={'preferences': 'vegetarian lunches'},
                headers=api_key_headers,
            )

    assert response.status_code == 200
    assert response.json()['preferences'] == 'vegetarian lunches'
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_api/test_state.py::test_get_state_returns_preferences tests/test_api/test_state.py::test_update_state_persists_preferences -v
```

Expected: both FAIL — `preferences` not in response schema yet.

- [ ] **Step 3: Add `preferences` to Pydantic models**

In `src/api/models.py`, update `StateResponse` and `UpdateStateRequest`:

```python
class StateResponse(BaseModel):
    """Response with current state."""
    current_day: str
    plan_id: str
    plan: List[DayPlan] = Field(default_factory=list)
    grocery_list: List[GroceryItem] = Field(default_factory=list)
    missing_macros: List[str] = Field(default_factory=list)
    grocery_inventory: List[dict] = Field(default_factory=list)
    unmatched_groceries: List[dict] = Field(default_factory=list)
    inventory_usage: dict = Field(default_factory=lambda: {"used": [], "unused": [], "supplemental": []})
    preferences: Optional[str] = None


class UpdateStateRequest(BaseModel):
    """Request to update state."""
    plan: Optional[List[DayPlan]] = None
    grocery_list: Optional[List[GroceryItem]] = None
    missing_macros: Optional[List[str]] = None
    current_day: Optional[str] = None
    grocery_inventory: Optional[List[dict]] = None
    unmatched_groceries: Optional[List[dict]] = None
    inventory_usage: Optional[dict] = None
    preferences: Optional[str] = None
```

- [ ] **Step 4: Update `GET /state/` to read and return `preferences`**

In `src/api/endpoints/state.py`, update the `get_state` function. Replace the `StateResponse(...)` call in the success path with:

```python
        return StateResponse(
            current_day=state.get('current_day', 'Monday'),
            plan_id=state.get('plan_id', 'unknown'),
            plan=state.get('plan', []),
            grocery_list=state.get('grocery_list', []),
            missing_macros=state.get('missing_macros', []),
            grocery_inventory=state.get('grocery_inventory', []),
            unmatched_groceries=state.get('unmatched_groceries', []),
            inventory_usage=state.get('inventory_usage', {"used": [], "unused": [], "supplemental": []}),
            preferences=state.get('preferences'),
        )
```

Also update the docstring for `get_state`:

```python
    """
    Get the current application state.

    Returns:
        StateResponse with current day, plan ID, plan, grocery list, missing macros,
        and preferences string.

    Example:
        GET /state/
    """
```

- [ ] **Step 5: Update `PUT /state/` to accept and persist `preferences`**

In `src/api/endpoints/state.py`, inside `update_state_endpoint`, add this block after the `inventory_usage` block:

```python
        if request.preferences is not None:
            update_data['preferences'] = request.preferences
```

Update the `StateResponse(...)` call in the success path to include `preferences`:

```python
        return StateResponse(
            current_day=merged_state.get('current_day', 'Monday'),
            plan_id=merged_state.get('plan_id', 'unknown'),
            plan=merged_state.get('plan', []),
            grocery_list=merged_state.get('grocery_list', []),
            missing_macros=merged_state.get('missing_macros', []),
            grocery_inventory=merged_state.get('grocery_inventory', []),
            unmatched_groceries=merged_state.get('unmatched_groceries', []),
            inventory_usage=merged_state.get('inventory_usage', {"used": [], "unused": [], "supplemental": []}),
            preferences=merged_state.get('preferences'),
        )
```

Also update the docstring for `update_state_endpoint`:

```python
    """
    Update the application state with new plan data.

    Args:
        request: UpdateStateRequest with optional plan, grocery_list, missing_macros,
                 current_day, and preferences string.

    Returns:
        StateResponse with updated state.

    Example:
        PUT /state/
        {
            "preferences": "high protein, no red meat"
        }
    """
```

- [ ] **Step 6: Run the two new tests to confirm they pass**

```bash
pytest tests/test_api/test_state.py::test_get_state_returns_preferences tests/test_api/test_state.py::test_update_state_persists_preferences -v
```

Expected: both PASS.

- [ ] **Step 7: Run the full state test suite to confirm no regressions**

```bash
pytest tests/test_api/test_state.py -v
```

Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add src/api/models.py src/api/endpoints/state.py tests/test_api/test_state.py
git commit -m "feat: add preferences field to state models and endpoints"
```

---

## Task 2: Frontend API layer — types and client

**Files:**
- Modify: `web/src/api/types.ts`
- Modify: `web/src/api/client.ts`

**Interfaces:**
- Produces: `AppState.preferences?: string`
- Produces: `api.state.update(body: Partial<AppState>): Promise<AppState>`

These changes carry no direct tests — they are verified by the component tests in Tasks 3 and 4.

---

- [ ] **Step 1: Add `preferences` to `AppState`**

In `web/src/api/types.ts`, update the `AppState` interface:

```ts
export interface AppState {
  current_day: string
  plan_id: string
  plan: DayPlan[]
  grocery_list: GroceryListItem[]
  missing_macros: string[]
  grocery_inventory: Record<string, unknown>[]
  unmatched_groceries: Record<string, unknown>[]
  inventory_usage: { used: string[]; unused: string[]; supplemental: string[] }
  preferences?: string
}
```

- [ ] **Step 2: Add `api.state.update` to the client**

In `web/src/api/client.ts`, update the `state` property of `api`:

```ts
  state: {
    get: () => request<AppState>('/state/'),
    update: (body: Partial<AppState>) =>
      request<AppState>('/state/', {
        method: 'PUT',
        body: JSON.stringify(body),
      }),
  },
```

- [ ] **Step 3: Commit**

```bash
git add web/src/api/types.ts web/src/api/client.ts
git commit -m "feat: add preferences to AppState type and api.state.update client method"
```

---

## Task 3: Plan page — placeholder, pre-fill from state, persist on generate

**Files:**
- Modify: `web/src/features/plan/PlanPage.tsx`
- Modify: `web/src/features/plan/PlanPage.test.tsx`

**Interfaces:**
- Consumes: `useAppState()` from `../state/hooks` → `{ data: AppState }`
- Consumes: `api.state.update` from `../../api/client`
- Consumes: `useQueryClient` from `@tanstack/react-query`

---

- [ ] **Step 1: Add a `beforeEach` default state mock to the test file**

Adding `useAppState` to `PlanPage` means it will call `GET /api/state/` on every render. The existing tests use `onUnhandledRequest: 'error'`, so they will fail without a state mock. Fix this by adding a `beforeEach` that registers a default empty-state handler before every test. Add this constant and hook after the existing `PLAN_DATA` constant in `web/src/features/plan/PlanPage.test.tsx`:

```ts
const EMPTY_STATE = {
  current_day: 'Monday',
  plan_id: '',
  plan: [],
  grocery_list: [],
  missing_macros: [],
  grocery_inventory: [],
  unmatched_groceries: [],
  inventory_usage: { used: [], unused: [], supplemental: [] },
  preferences: undefined,
}

beforeEach(() => {
  server.use(
    http.get('http://localhost/api/state/', () => HttpResponse.json(EMPTY_STATE))
  )
})
```

- [ ] **Step 2: Write the two failing tests**

Add these tests inside the `describe('PlanPage', ...)` block in `web/src/features/plan/PlanPage.test.tsx`:

```ts
  it('pre-fills preferences input from stored state', async () => {
    server.use(
      http.get('http://localhost/api/plan/', () => HttpResponse.json(PLAN_DATA)),
      http.get('http://localhost/api/state/', () =>
        HttpResponse.json({ ...EMPTY_STATE, preferences: 'high protein' })
      )
    )
    renderPlanPage()
    const input = await screen.findByPlaceholderText(/e\.g\. no red meat/i)
    expect(input).toHaveValue('high protein')
  })

  it('persists preferences to state after successful plan generation', async () => {
    let putBody: unknown = null
    server.use(
      http.get('http://localhost/api/plan/', () => HttpResponse.json(PLAN_DATA)),
      http.get('http://localhost/api/state/', () =>
        HttpResponse.json({ ...EMPTY_STATE, preferences: 'high protein' })
      ),
      http.post('http://localhost/api/plan/generate', () => HttpResponse.json(PLAN_DATA)),
      http.put('http://localhost/api/state/', async ({ request }) => {
        putBody = await request.json()
        return HttpResponse.json({ ...EMPTY_STATE, preferences: 'high protein' })
      })
    )
    renderPlanPage()
    await screen.findByRole('button', { name: /generate plan/i })
    fireEvent.click(screen.getByRole('button', { name: /generate plan/i }))
    await waitFor(() => expect(putBody).toMatchObject({ preferences: 'high protein' }))
  })
```

- [ ] **Step 3: Run the new tests to confirm they fail**

From `web/`:

```bash
npm test -- --run --reporter=verbose 2>&1 | grep -A3 "pre-fills\|persists preferences"
```

Expected: both FAIL — `PlanPage` does not yet call state or persist preferences.

- [ ] **Step 4: Update `PlanPage.tsx`**

Replace the entire contents of `web/src/features/plan/PlanPage.tsx` with:

```tsx
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../api/client'
import { Card } from '../../components/Card'
import { ErrorBanner } from '../../components/ErrorBanner'
import { Spinner } from '../../components/Spinner'
import { useAppState } from '../state/hooks'
import { usePlan, useGeneratePlan } from './hooks'

export function PlanPage() {
  const { data: planData, isLoading, isError, error } = usePlan()
  const { data: appState } = useAppState()
  const generate = useGeneratePlan()
  const qc = useQueryClient()
  const [selectedDay, setSelectedDay] = useState('')
  const [preferences, setPreferences] = useState('')
  const prefInitialized = useRef(false)

  const days = planData?.plan ?? []

  useEffect(() => {
    if (days.length > 0 && !selectedDay) {
      setSelectedDay(days[0].day)
    }
  }, [days, selectedDay])

  useEffect(() => {
    if (appState !== undefined && !prefInitialized.current) {
      setPreferences(appState.preferences ?? '')
      prefInitialized.current = true
    }
  }, [appState])

  if (isLoading) return <Spinner />
  if (isError)
    return (
      <ErrorBanner
        message={error instanceof ApiError ? error.message : 'Failed to load plan'}
      />
    )

  const currentDayPlan = days.find((d) => d.day === selectedDay) ?? days[0]

  function handleGenerate() {
    generate.mutate(
      { preferences: preferences || undefined },
      {
        onSuccess: async () => {
          await api.state.update({ preferences: preferences || undefined })
          qc.invalidateQueries({ queryKey: ['state'] })
        },
      }
    )
  }

  return (
    <div>
      <div className="flex gap-3 mb-6">
        <input
          type="text"
          placeholder="e.g. no red meat, high protein, vegetarian lunches"
          value={preferences}
          onChange={(e) => setPreferences(e.target.value)}
          className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        <button
          onClick={handleGenerate}
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
                {currentDayPlan.total_calories} cal total · {currentDayPlan.total_protein}g protein ·{' '}
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

- [ ] **Step 5: Run the full Plan page test suite**

```bash
npm test -- --run --reporter=verbose 2>&1 | grep -E "PlanPage|PASS|FAIL"
```

Expected: all tests PASS, including the two new ones.

- [ ] **Step 6: Commit**

```bash
git add web/src/features/plan/PlanPage.tsx web/src/features/plan/PlanPage.test.tsx
git commit -m "feat: pre-fill and persist preferences on Plan page"
```

---

## Task 4: State page — preferences section, Save, and Regenerate Plan

**Files:**
- Modify: `web/src/features/state/hooks.ts`
- Modify: `web/src/features/state/StatePage.tsx`
- Modify: `web/src/features/state/StatePage.test.tsx`

**Interfaces:**
- Consumes: `api.state.update` from `../../api/client`
- Consumes: `useGeneratePlan` from `../plan/hooks`
- Produces: `useUpdateState()` mutation hook

---

- [ ] **Step 1: Write the four failing tests**

Add these tests inside the `describe('StatePage', ...)` block in `web/src/features/state/StatePage.test.tsx`:

```ts
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
```

- [ ] **Step 2: Run the new tests to confirm they fail**

```bash
npm test -- --run --reporter=verbose 2>&1 | grep -A3 "preferences input\|Save button\|Regenerate"
```

Expected: all five FAIL.

- [ ] **Step 3: Add `useUpdateState` to `web/src/features/state/hooks.ts`**

Replace the entire file with:

```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import type { AppState } from '../../api/types'

export function useAppState() {
  return useQuery({ queryKey: ['state'], queryFn: api.state.get })
}

export function useUpdateState() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (updates: Partial<AppState>) => api.state.update(updates),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['state'] }),
  })
}
```

- [ ] **Step 4: Update `StatePage.tsx` to add the Preferences section**

Replace the entire contents of `web/src/features/state/StatePage.tsx` with:

```tsx
import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ApiError } from '../../api/client'
import { ErrorBanner } from '../../components/ErrorBanner'
import { Spinner } from '../../components/Spinner'
import { Table } from '../../components/Table'
import { useGeneratePlan } from '../plan/hooks'
import { useAppState, useUpdateState } from './hooks'

export function StatePage() {
  const { data: state, isLoading, isError, error } = useAppState()
  const updateState = useUpdateState()
  const generatePlan = useGeneratePlan()
  const qc = useQueryClient()
  const [preferencesInput, setPreferencesInput] = useState('')
  const prefInitialized = useRef(false)

  useEffect(() => {
    if (state !== undefined && !prefInitialized.current) {
      setPreferencesInput(state.preferences ?? '')
      prefInitialized.current = true
    }
  }, [state])

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
        <h2 className="text-lg font-semibold mb-3">Preferences</h2>
        <div className="flex gap-3 max-w-lg">
          <input
            type="text"
            value={preferencesInput}
            onChange={(e) => setPreferencesInput(e.target.value)}
            placeholder="e.g. no red meat, high protein, vegetarian lunches"
            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            onClick={() => updateState.mutate({ preferences: preferencesInput || undefined })}
            disabled={updateState.isPending}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-sm font-medium"
          >
            {updateState.isPending ? 'Saving…' : 'Save'}
          </button>
        </div>
        {state.plan_id && (
          <button
            onClick={() =>
              generatePlan.mutate(
                { preferences: preferencesInput || undefined },
                { onSuccess: () => qc.invalidateQueries({ queryKey: ['state'] }) }
              )
            }
            disabled={generatePlan.isPending}
            className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
          >
            {generatePlan.isPending ? 'Regenerating…' : 'Regenerate Plan'}
          </button>
        )}
      </section>

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

- [ ] **Step 5: Run the full frontend test suite**

```bash
npm test -- --run --reporter=verbose
```

Expected: all tests PASS across `PlanPage`, `StatePage`, and other test files.

- [ ] **Step 6: Commit**

```bash
git add web/src/features/state/hooks.ts web/src/features/state/StatePage.tsx web/src/features/state/StatePage.test.tsx
git commit -m "feat: add preferences section and Regenerate Plan button to State page"
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Task |
|-------------|------|
| Placeholder on Plan page preferences input | Task 3 |
| Pre-fill Plan page input from stored state | Task 3 |
| Persist preferences to state after plan generation | Task 3 |
| State page shows preferences in editable input | Task 4 |
| Save button on State page calls PUT /state/ | Task 4 |
| Regenerate Plan button visible only when plan_id non-empty | Task 4 |
| Regenerate Plan calls POST /plan/generate with stored preferences | Task 4 |
| GET /state/ and PUT /state/ docstrings updated | Task 1 |
| Sample curl calls in PR | In spec doc; engineer adds to PR body |
| All new behaviour covered by tests | Tasks 1, 3, 4 |

All requirements covered. No placeholders. Types are consistent (`preferences?: string` / `Optional[str]`) across all tasks.
