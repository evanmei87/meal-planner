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

### Meal Generation Pipeline

1. Load `state.json` + static data files
2. Calculate TDEE from `src/data/user_stats.csv` (falls back to defaults)
3. Score candidate meals by inventory ingredient overlap (perishables weighted ×2)
4. Generate each day from current day through Sunday, cycling fallback slots by day index on Friday with +450 cal target (pre-long-run)
5. Compute supplemental grocery list (ingredients not covered by inventory)
6. Persist updated state

## Planning

Plans go in `/plan/issue-{number}-{feature-name}/plan.md`. Use `0` when no GitHub issue exists. Include a link to the originating GitHub issue near the top of every plan file.
