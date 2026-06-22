# Food & Nutrition Intelligence: 7-Day Meal Planner

An AI-driven meal planning assistant that generates personalized 7-day meal plans, tracks nutritional intake, manages grocery inventory, and supports saved meals — all accessible through a web UI.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the App](#running-the-app)
- [Using the Web UI](#using-the-web-ui)
- [Data & Configuration](#data--configuration)
- [Confidence Scoring](#confidence-scoring)
- [Development](#development)
- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [License](#license)

## Features

- Generate 7-day meal plans aligned with user preferences and nutritional goals
- Track nutritional macros and caloric intake
- Manage grocery lists and grocery inventory with natural-language input
- Save, list, and search reusable meals
- Persist state across sessions

## Prerequisites

- [mise](https://mise.jdx.dev) — tool version manager (manages Node.js)
- [uv](https://docs.astral.sh/uv/) — Python package and project manager

## Setup

### 1. Install dependencies

```bash
# Install Python and Node versions declared in mise.toml
mise install

# Install Python dependencies
uv sync

# Install frontend dependencies
cd web && npm install && cd ..
```

### 2. Configure environment variables

**Backend** — copy the example and fill in your keys:

PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

macOS/Linux:

```bash
cp .env.example .env
nano .env
```

Your `.env` should contain:

```env
MEAL_PLANNER_API_KEY=dev-key-change-in-production
GEMINI_API_KEY=your-gemini-api-key-here
```

- `MEAL_PLANNER_API_KEY` — required by the API server. For local development, `dev-key-change-in-production` is the default.
- `GEMINI_API_KEY` — used for LLM-backed grocery parsing. Create one at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).

**Frontend** — copy the web example:

PowerShell:

```powershell
Copy-Item web\.env.example web\.env
```

macOS/Linux:

```bash
cp web/.env.example web/.env
```

Your `web/.env` should contain:

```env
VITE_API_KEY=dev-key-change-in-production
```

This must match `MEAL_PLANNER_API_KEY` in your backend `.env`.

Never commit either `.env` file to version control.

## Running the App

The web UI requires both the API server and the frontend dev server to be running. Open two terminals:

**Terminal 1 — API server:**

```bash
uv run uvicorn src.api.main:app --reload
```

The API starts at `http://localhost:8000`.

**Terminal 2 — Frontend dev server:**

```bash
cd web
npm run dev
```

The web UI starts at `http://localhost:5173`. Open that URL in your browser.

## Using the Web UI

The app has four sections, accessible from the top navigation bar:

### Plan

View your current 7-day meal plan. Switch between days using the day selector. Each meal card shows name, calories, and macros and links to the meal's detail page. Click **Generate Plan** to create a new plan (optionally enter preferences in the text field first).

### Meals

Browse your saved meals in a searchable table. Use the search bar to filter by name. Click **Add Meal** to save a new meal with ingredients, macros, instructions, category, and tags. Click any meal name to view its full detail page.

### Groceries

Add groceries using natural language — type something like "I got two pounds of chicken thighs, a bag of spinach, and some Greek yogurt" and press **Add**. The app parses the text and shows a result table with standardized items, quantities, confidence scores, and save status. Your current grocery list and inventory are displayed below.

### State

Read-only view of your current day, plan ID, inventory usage (used, unused, supplemental), unmatched groceries, and missing macros.

## Data & Configuration

The planner reads preferences, foods, recipes, and state from `src/data/` and `src/state/`:

- `src/data/food.csv` — standardized food database
- `src/data/specialty-ingredients.md` — specialty food items and macros
- `src/data/rules.md` — hard constraints, allergies, and dislikes
- `src/data/meal-recipes.md` — reusable meal recipes
- `src/data/user_stats.csv` — optional personal metrics for TDEE calculation
- `src/state/state.json` — generated plans, grocery lists, inventory, and session state

If `user_stats.csv` is not present, the planner falls back to default stats.

## Confidence Scoring

LLM-assisted grocery parsing uses a normalized `0.0–1.0` confidence scale:

- `>= 0.7` — high confidence; auto-saved to inventory
- `0.4–0.699` — review confidence; presented for confirmation
- `< 0.4` — low confidence; requires manual macro entry

## Development

Run backend tests:

```bash
uv run pytest tests/
```

Run frontend tests:

```bash
cd web && npm run test:run
```

Format and type check (backend):

```bash
uv run black src/
uv run mypy src/
```

Type check (frontend):

```bash
cd web && npx tsc --noEmit
```

For CLI and direct API server usage, see [docs/cli-reference.md](docs/cli-reference.md).

## Architecture Overview

The frontend (`web/`) is a React + Vite SPA that talks exclusively to the FastAPI backend through a typed API client. The Vite dev server proxies `/api/*` requests to `http://localhost:8000`, so the frontend never needs to know the backend's address directly.

### State Management

- Session state is persisted in `src/state/state.json`
- State includes profile, preferences, generated meals, grocery items, and inventory
- The frontend uses TanStack Query for server-state caching and invalidation

### Generation Pipeline

1. Calculate TDEE
2. Load preferences, foods, recipes, and rules
3. Generate meals
4. Build grocery list
5. Persist state

## Project Structure

```text
meal-planner/
├── README.md
├── docs/
│   └── cli-reference.md     # CLI and direct API server usage
├── pyproject.toml
├── requirements.txt
├── main.py                  # Command CLI entry point
├── src/
│   ├── api/
│   │   ├── main.py
│   │   └── endpoints/
│   ├── data/
│   │   ├── food.csv
│   │   ├── specialty-ingredients.md
│   │   ├── meal-recipes.md
│   │   ├── rules.md
│   │   └── user_stats.csv
│   ├── state/
│   │   └── state.json
│   ├── tools/
│   └── server.py            # Interactive CLI entry point
├── web/                     # React frontend
│   ├── src/
│   │   ├── api/             # Typed API client
│   │   ├── features/        # plan, meals, groceries, state
│   │   └── components/      # Shared UI components
│   └── package.json
└── tests/
```

## License

MIT
