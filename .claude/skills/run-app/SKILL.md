---
name: run-app
description: Use when the user asks to run, start, launch, or open the meal-planner app, or wants to validate changes in the browser.
---

# Run Meal-Planner App

Launch both servers so the user can open the app in a browser.

## Commands

Run both via the **Bash tool** (not PowerShell) from the project root (`C:\Users\terro\workspace\projects\meal-planner`):

```bash
# Backend — FastAPI on port 8000
uv run uvicorn src.api.main:app --reload > /tmp/backend.log 2>&1 &

# Frontend — Vite dev server on port 5173
cd web && npm run dev > /tmp/frontend.log 2>&1 &
```

## Verify

```bash
sleep 4
# Backend up if uvicorn line appears:
grep "Uvicorn running" /tmp/backend.log
# Frontend up if Local: line appears:
grep "Local:" /tmp/frontend.log
```

## Tell the user

Once both are confirmed running:

> Backend: http://localhost:8000  
> Frontend: http://localhost:5173  
> Open http://localhost:5173 in your browser.

## Notes

- Both servers must run simultaneously — Vite proxies `/api/*` → port 8000.
- `MEAL_PLANNER_API_KEY` and `VITE_API_KEY` must match; both read from `.env` at project root.
- `GEMINI_API_KEY` required for preference normalization (also in `.env`).
- If port already in use, the previous process is likely still running — no action needed.
