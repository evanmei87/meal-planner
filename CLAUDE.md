# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Priority order:** User-level rules (`~/.claude/rules/`) and installed skills always take precedence over this file. Then project-specific instructions below.

## Commands

**Backend:**
```bash
uv run uvicorn src.api.main:app --reload   # API server at http://localhost:8000
uv run pytest tests/ -q                    # all backend tests
uv run pytest tests/path/to/test.py::test_name -q  # single test
uv run black src/
uv run mypy src/
```

**Frontend** (from `web/`):
```bash
npm run dev          # dev server at http://localhost:5173
npm test -- --run    # all frontend tests (vitest)
npx tsc --noEmit     # type check
```

Both servers must run simultaneously. The Vite dev server proxies `/api/*` → `http://127.0.0.1:8000`, stripping the `/api` prefix before forwarding.

## Architecture

**Stack:** React + TypeScript + Vite SPA (`web/`) backed by FastAPI (`src/api/`), with a Python tools layer (`src/tools/`) and file-based state (`src/state/state.json`).

### Request Flow

```
Browser → Vite proxy /api/* → FastAPI (port 8000) → src/tools/
```

All frontend HTTP goes through `web/src/api/client.ts` — components never call `fetch` directly. The `api` object there maps to four resource groups: `plan`, `meals`, `state`, `groceries`.

All backend routes require `X-API-Key` header validated in `src/api/main.py:get_api_key`. The key is set by `MEAL_PLANNER_API_KEY` (backend) and must match `VITE_API_KEY` (frontend).

Frontend files live exclusively under `web/` — never add them to the Python `src/` tree. Follow existing code style exactly: Tailwind classes, naming conventions, import order.

### Backend Structure

- `src/api/endpoints/` — one file per resource (`meal_plan.py`, `meals.py`, `state.py`, `groceries.py`). Every new router must be added to `main.py` behind `Security(get_api_key)`.
- `src/tools/` — business logic: `generate_plan.py` (meal generation pipeline), `food_processor.py` + `llm_agent.py` (LLM-backed grocery parsing via Gemini), `grocery_inventory.py` (inventory CRUD), `confidence.py` (0.0–1.0 scoring: ≥0.7 auto-save, 0.4–0.699 review, <0.4 manual).
- `src/data/` — static files read at runtime: `food.csv`, `specialty-ingredients.md`, `rules.md`, `meal-recipes.md`, `user_stats.csv`.
- `src/state/state.json` — single mutable file holding plan, grocery list, inventory, and session state. Loaded and saved by `generate_plan.py:load_state`/`save_state`.

### Frontend Structure

- `web/src/api/` — `client.ts` (typed fetch wrapper), `types.ts` (all shared interfaces).
- `web/src/features/` — four feature directories (`plan/`, `meals/`, `groceries/`, `state/`), each with a `Page.tsx` and `hooks.ts`. Hooks use TanStack Query.
- TanStack Query keys: `['plan']`, `['meals']`, `['meals', 'search', params]`, `['state']`.

### Design System

Before writing or editing anything under `web/src/features/`, read `.design-sync/north-star.md`. It holds every design invariant and is the single source for them.

Tier 1 invariants are enforced automatically: a `Stop` hook runs `node .design-sync/check/ds-check.mjs --gate` and fails the turn if any violation count rises above `.design-sync/check/baseline.json`. Fix new violations rather than raising the baseline — the baseline only ever moves down, automatically, and a manual increase is a reviewable change requiring justification.

Tier 2 invariants are visual and cannot be linted, so they are not gated. Instead the hook reports when `/ds-review` is overdue — that is, when `className` values in `web/src/features/` changed since the last review.

**When the hook reports Tier 2 is stale, offer the review** — do not silently skip it and do not run it unprompted. Raise it at a natural boundary: before committing or pushing, or when reporting a chunk of visual work complete. Say that Tier 1 passed, that Tier 2 is overdue, and ask whether to run `/ds-review`. It needs both servers and a browser session, so it is the user's call, but the offer is not optional.

To check on demand: `node .design-sync/check/ds-check.mjs`

### Meal Generation Pipeline

1. Load `state.json` + static data files
2. Calculate TDEE from `src/data/user_stats.csv` (falls back to defaults)
3. Score candidate meals by inventory ingredient overlap (perishables weighted ×2)
4. Generate each day from current day through Sunday, cycling fallback slots by day index on Friday with +450 cal target (pre-long-run)
5. Compute supplemental grocery list (ingredients not covered by inventory)
6. Persist updated state

## External APIs

### Gemini API (Google AI)

Used for:
- **Grocery parsing** (`src/tools/food_processor.py` + `src/tools/llm_agent.py`)
- **Preference normalization** (`src/tools/preference_normalizer.py`) — called once when user saves preferences

**Setup:** Set `GEMINI_API_KEY` in a `.env` file at the project root. The key is read by `_read_env_file_api_key()` in `src/tools/llm_agent.py`.

```
GEMINI_API_KEY=your-key-here
```

**Model:** `gemini-2.5-flash-lite` (configured as `DEFAULT_MODEL` in `llm_agent.py`).

**Free tier:** Available at [ai.google.dev](https://ai.google.dev). Google does not publish static rate-limit numbers — check your current limits in [AI Studio → Rate Limits](https://aistudio.google.com/rate-limit). As of mid-2026 the free tier supports on the order of tens of requests per minute and hundreds to low thousands per day for Flash-class models. See [pricing page](https://ai.google.dev/gemini-api/docs/pricing) for input/output token costs on paid tier.

**Calls per user action:**
| Action | Gemini calls |
|--------|-------------|
| Save preferences (PUT /state/) | 1 — preference normalization |
| Parse groceries (POST /groceries/) | 1 per parse request |
| Regenerate plan (POST /plan/generate) | 0 |

Preference normalization only fires on explicit Save, so a typical session makes 1–3 Gemini calls total. The free tier is more than sufficient for personal or development use. If the API key is missing or the call fails, preference normalization falls back to simple keyword matching — the app stays functional.

## Planning

Plans go in `/plan/issue-{number}-{feature-name}/plan.md`. Use `0` when no GitHub issue exists. Include a link to the originating GitHub issue near the top of every plan file.

Plan files are always committed to git. When creating a PR, stage and commit all files under `plan/` before pushing.
