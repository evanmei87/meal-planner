# Web Frontend Design: React SPA for the Meal Planner API

## Summary

Build a React single-page web frontend that consumes the existing FastAPI
backend, covering meal plans, saved meals, groceries/inventory, and a read-only
state view. The frontend lives in a new `web/` directory at the repo root and is
fully decoupled from the backend's persistence — it talks only to the REST API
through one typed client. The single backend change is a new `POST /groceries`
endpoint that exposes the existing natural-language grocery parser (currently
CLI-only) over HTTP by reusing the existing `tools/` layer.

## Goals

- Surface all four backend capability areas in a usable web UI: meal plans,
  saved meals, groceries + inventory, and current state.
- Expose natural-language grocery parsing to the web via a new API endpoint.
- Keep the frontend storage-agnostic so a future move to Supabase/AWS requires
  **no frontend changes** — only backend `tools/` internals change.

## Non-Goals (v1)

- No profile/state editing UI (`PUT /state/` is not surfaced in v1; state view
  is read-only).
- No authentication beyond the existing `X-API-Key` header (single-user local
  tool).
- No speculative storage-abstraction layer in the backend. The existing
  `tools/` layer already is the persistence seam; we respect it rather than
  rebuild it.

## Decisions

| Decision | Choice |
|----------|--------|
| Framework | React + Vite + TypeScript |
| Styling | Tailwind CSS (no component library) |
| Routing | React Router |
| Server state | TanStack Query (React Query) |
| Run model | Vite dev server; `/api` proxied to `http://localhost:8000` |
| Auth | `X-API-Key` read from `web/.env` (`VITE_API_KEY`), injected by the API client |
| Testing | Vitest + React Testing Library + MSW; pytest for the new endpoint |

## Architecture

### Project Layout

```text
meal-planner/
├── src/                    # existing Python backend (only addition: groceries endpoint)
└── web/
    ├── .env                # VITE_API_KEY=dev-key-change-in-production
    ├── .env.example
    ├── vite.config.ts      # dev proxy: /api -> http://localhost:8000
    ├── tailwind.config.ts
    ├── index.html
    └── src/
        ├── main.tsx            # app entry: Router + QueryClient providers
        ├── App.tsx             # layout shell + nav
        ├── api/
        │   ├── client.ts       # fetch wrapper; injects X-API-Key; maps errors to ApiError
        │   └── types.ts        # TS types mirroring the Pydantic models
        ├── features/
        │   ├── plan/           # hooks + components for meal plan
        │   ├── meals/          # saved meals (list, search, add, detail)
        │   ├── groceries/      # grocery list + inventory + NL add
        │   └── state/          # state/profile read view
        └── components/         # shared UI (Table, Card, Spinner, ErrorBanner)
```

### Layering Rule

Components never call `fetch` directly. Each feature exposes query/mutation
hooks (e.g. `usePlan()`, `useGeneratePlan()`, `useMeals()`, `useAddGroceries()`)
that call the typed `api/client.ts`. This keeps API concerns isolated per
feature and components purely presentational, supporting local reasoning and
MSW-based testing.

### Decoupling / Future Cloud Storage

Two boundaries keep a future Supabase/AWS migration painless:

1. **Backend:** the new `POST /groceries` endpoint reuses the existing `tools/`
   functions (`parse_ingredients`, `get_ingredient_metadata`,
   `add_inventory_items`, `add_unmatched_items`) and never touches files
   directly. Persistence lives behind that tools layer today (the `state.json`
   reads/writes). Swapping to a cloud store changes those tool internals only.
2. **Frontend:** React talks only to the REST API through `api/client.ts` and
   has zero knowledge of backend persistence. A storage migration requires no
   frontend changes.

## Feature Pages

### `/plan` — Meal Plan

- "Generate plan" button → `POST /plan/generate` with an optional preferences
  text field.
- Day selector (Mon–Sun). Each day renders its meals as cards showing name,
  calories, macros, and ingredients, plus daily totals.
- Reads the current plan via `GET /plan/`.
- Each meal card links to `/meals/:name` (URL-encoded meal name). The resulting
  grocery list links to the groceries view.

### `/meals` — Saved Meals

- Table of saved meals (name, category, macros) from `GET /meals/`.
- Search/filter bar mapping to `GET /meals/search` (category, macro min/max,
  ingredient, tag, search term).
- "Add meal" form → `POST /meals/add` (name, ingredients, macros, instructions,
  category, tags). On success the list query is invalidated and refetches.

### `/meals/:name` — Meal Detail (plan deep-link target)

- Fetches saved meals and shows the one matching `name` (full ingredients,
  instructions, macros, tags).
- **Edge case:** a meal in a generated plan is not guaranteed to be a saved
  meal. When no saved meal matches `name`, the view shows the plan meal's basic
  info (name, calories, macros carried from the plan) with a note that it is not
  in the saved library — not a dead 404. `name` is the only shared identifier
  between a plan `MealItem` and a saved `MealResponse`.

### `/groceries` — Groceries & Inventory

- Natural-language add box ("I got two pounds of chicken thighs…") → new
  `POST /groceries` endpoint. Shows the parse-result table (raw → standardized,
  quantity, unit, match, confidence, status), mirroring the CLI output.
- Current grocery list and inventory tables from `GET /state/`.
- On a successful add, the state query is invalidated so the inventory refreshes.

### `/state` — State / Profile (read-only)

- Read view of current day, plan id, inventory usage
  (`{used, unused, supplemental}`), and unmatched groceries from `GET /state/`.

## Backend Addition: `POST /groceries`

The only backend change. Wraps the existing CLI grocery-parsing pipeline.

- **Request:** `{ "text": "<natural language grocery description>" }`.
- **Behavior:** mirrors `groceries_add_text` in `main.py` — calls
  `parse_ingredients(text)`, then `get_ingredient_metadata` per item, auto-saves
  high-confidence Corgis matches via `add_inventory_items`, and records the rest
  via `add_unmatched_items`.
- **Response:** the parsed result rows (raw_phrase, standardized_item, quantity,
  unit, match/source, confidence_score, confidence_level, status) plus a summary
  of saved vs. review/manual counts.
- **Constraint:** the endpoint must reuse the `tools/` functions and must not
  read or write state files directly, preserving the storage seam.
- Lives in a new router (e.g. `src/api/endpoints/groceries.py`) registered in
  `src/api/main.py` behind the existing `Security(get_api_key)` dependency, with
  request/response Pydantic models added to `src/api/models.py`.

## API Surface Consumed

All endpoints require the `X-API-Key` header (injected by `api/client.ts`).

| Method | Path | Used by |
|--------|------|---------|
| POST | `/plan/generate` | Plan page generate button |
| GET | `/plan/` | Plan page current plan |
| GET | `/plan/{day}` | Plan page day selector (optional; `/plan/` may suffice) |
| GET | `/meals/` | Saved meals list, meal detail |
| GET | `/meals/search` | Saved meals filter bar |
| POST | `/meals/add` | Add-meal form |
| GET | `/state/` | Groceries view, state view |
| POST | `/groceries` | Grocery NL-add box (**new**) |

`PUT /state/` exists but is not surfaced in v1.

## Error Handling

- `api/client.ts` centralizes error handling: non-2xx responses throw a typed
  `ApiError` (status + message). A `401` surfaces a clear "check your API key in
  `web/.env`" message instead of a generic failure.
- TanStack Query exposes `isLoading` / `isError` per hook; each page renders a
  shared `<Spinner/>` while loading and `<ErrorBanner/>` on error. No bare
  unhandled rejections.
- Mutations (generate plan, add meal, add groceries) show inline
  pending/success/error feedback and invalidate the relevant queries on success
  so views refresh automatically.

## Testing

Vitest + React Testing Library + MSW for the frontend; pytest for the backend.

- **API client:** unit tests for header injection, error mapping (401 →
  friendly message), and JSON parsing.
- **Feature hooks/components** (MSW-mocked endpoints):
  - Plan renders days, meals, and macro totals.
  - Meal search filters the list.
  - Grocery NL-add renders the parse-result table.
  - Plan meal links route to `/meals/:name`.
  - Meal detail "not a saved meal" fallback renders for an unmatched name.
- **Backend:** a pytest for `POST /groceries` — valid text yields a parsed
  inventory result and reuses the tools layer (no direct file access asserted by
  using the existing tools' behavior).

## Open Questions

None outstanding. Profile editing and authentication hardening are deferred to a
future iteration.
