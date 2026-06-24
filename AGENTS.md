# AGENTS.md

Development guide for AI agents working in this repository.

> **Priority order:** User-level rules (`~/.claude/rules/`) and installed skills always take precedence over this file. Then project-specific instructions below.

## Repository Overview

Meal planner web app with a React + TypeScript frontend (`web/`), FastAPI backend (`src/api/`), and a Python tools layer (`src/tools/`).

## Planning

All plans and documentation produced by planning skills (e.g. `superpowers:writing-plans`) go in `/plan/`.

### Directory naming

Format: `/plan/issue-{issue-number}-{feature-name}/`

Use `0` as the issue number when no GitHub issue exists.

Examples:
- `/plan/issue-5-improve-preferences/plan.md`
- `/plan/issue-0-web-frontend/plan.md`

### Required in every plan

Every plan file must include a link to the originating GitHub issue near the top:

```
GitHub Issue: https://github.com/evanmei87/meal-planner/issues/{number}
```

If no issue exists, omit this line.

## Running Tests

- **Backend** (from repo root): `uv run pytest tests/ -q`
- **Frontend** (from `web/`): `npm test -- --run`

## Key Conventions

- All frontend files live under `web/`. Never add frontend files to the Python `src/` tree.
- Components never call `fetch` directly — always go through `api/client.ts`.
- All new backend routes must be registered behind `Security(get_api_key)` in `src/api/main.py`.
- Follow existing code style exactly: Tailwind classes, naming conventions, import order.
- Query keys: `['plan']` for the meal plan, `['meals']` for the meals list, `['meals', 'search', params]` for search, `['state']` for app state.
