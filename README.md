# Food & Nutrition Intelligence: 7-Day Meal Planner

An AI-driven meal planning assistant that generates personalized 7-day meal plans, tracks nutritional intake, manages grocery inventory, supports saved meals, and exposes both CLI and FastAPI interfaces.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Setup](#environment-setup)
- [Ways to Run](#ways-to-run)
  - [1. Interactive Meal Planner CLI](#1-interactive-meal-planner-cli)
  - [2. Command CLI](#2-command-cli)
  - [3. REST API Server](#3-rest-api-server)
- [Data Loaded at Startup](#data-loaded-at-startup)
- [Confidence Scoring](#confidence-scoring)
- [Inventory-Aware Meal Generation](#inventory-aware-meal-generation)
- [Saved Meals](#saved-meals)
- [Configuration](#configuration)
- [Development](#development)
- [Architecture Overview](#architecture-overview)
  - [State Management](#state-management)
  - [Generation Pipeline](#generation-pipeline)
- [Project Structure](#project-structure)
- [License](#license)

## Features

- Generate 7-day meal plans aligned with user preferences and nutritional goals
- Track nutritional macros and caloric intake
- Manage grocery lists and grocery inventory
- Save, list, and search reusable meals
- Persist state across sessions
- Expose meal planning workflows through a REST API

## Prerequisites

- [mise](https://mise.jdx.dev) - tool version manager
- [uv](https://docs.astral.sh/uv/) - Python package and project manager

## Installation

```bash
# Install the Python version specified in your mise configuration
mise install

# Create a virtual environment using uv
uv venv

# Install Python dependencies
uv pip install -r requirements.txt

# If pyproject.toml is fully configured for uv, this may also work
uv sync
```

## Environment Setup

Some workflows call the API or LLM-backed grocery parsing. Create a local `.env` file from the example file, then set your keys.

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

Your `.env` file should contain:

```env
MEAL_PLANNER_API_KEY=dev-key-change-in-production
GEMINI_API_KEY=your-gemini-api-key-here
```

### Environment Variables

- `MEAL_PLANNER_API_KEY` - API key required by authenticated FastAPI endpoints. For local development, `dev-key-change-in-production` matches the default used by the app.
- `GEMINI_API_KEY` - Gemini API key used for LLM-backed grocery parsing and ingredient matching. Create one at `https://aistudio.google.com/app/apikey`.

Never commit `.env` to version control. For production or shared environments, replace `dev-key-change-in-production` with a stronger `MEAL_PLANNER_API_KEY`.

## Ways to Run

This project has three main entry points. Use the one that matches how you want to interact with the service.

### 1. Interactive Meal Planner CLI

Run the prompt-based meal planner interface:

```bash
uv run src/server.py
```

Use this when you want an interactive terminal session with commands like:

```text
show_profile
generate_plan
show_groceries
add_groceries I got two pounds boneless chicken thighs, spinach, and half a pound of salmon.
show_inventory
clear_inventory
help
exit
```

This entry point also includes helper commands that call the REST API if the API server is running:

```text
api plan generate
api meals list
api meals search bowl
api state get
```

By default, API helper commands target `http://localhost:8000`. Override with:

PowerShell:

```powershell
$env:MEAL_PLANNER_API_URL = "http://localhost:8000"
uv run src/server.py
```

macOS/Linux:

```bash
MEAL_PLANNER_API_URL=http://localhost:8000 uv run src/server.py
```

### 2. Command CLI

Run one-off commands for saved meals, meal generation, and grocery inventory:

```bash
uv run main.py --help
```

Generate a meal plan:

```bash
uv run main.py generate
```

Add groceries from natural language:

```bash
uv run main.py groceries add --text "I got two pounds boneless chicken thighs, spinach, and half a pound of salmon."
```

List or clear grocery inventory:

```bash
uv run main.py groceries list
uv run main.py groceries clear
```

Add a saved meal:

```bash
uv run main.py add \
  --name "Chicken & Rice Bowl" \
  --ingredients "Chicken Breast, White Rice, Broccoli" \
  --macros "450|35|50|12" \
  --instructions "Cook chicken in a pan;Cook rice in a pot;Steam broccoli;Combine everything" \
  --category "Dinner" \
  --tags "high_protein,quick"
```

List saved meals:

```bash
uv run main.py list
uv run main.py list --category Breakfast
uv run main.py list --search "bowl"
uv run main.py list --format verbose
```

Search saved meals:

```bash
uv run main.py search --category Lunch
uv run main.py search --min-cal 300 --max-cal 600 --min-prot 20
uv run main.py search --ingredient "Chicken Breast"
uv run main.py search --tag "high_protein"
uv run main.py search --category Dinner --min-cal 400 --tag "quick"
```

Supported search filters: `--category`, `--search`, `--min-cal`, `--max-cal`, `--min-prot`, `--max-prot`, `--min-carb`, `--max-carb`, `--min-fat`, `--max-fat`, `--ingredient`, `--tag`.

### 3. REST API Server

Start the FastAPI server:

```bash
uv run uvicorn src.api.main:app
```

For development with automatic reload:

```bash
uv run uvicorn src.api.main:app --reload
```

The API is available at:

```text
http://localhost:8000
```

Interactive API docs are available at:

```text
http://localhost:8000/docs
```

Authenticated endpoints require the `X-API-Key` header:

```bash
curl -H "X-API-Key: dev-key-change-in-production" http://localhost:8000/state/
```

## Data Loaded at Startup

The planner reads preferences, foods, recipes, and state from `src/data/` and `src/state/`:

- `src/data/food.csv` - standardized food database
- `src/data/specialty-ingredients.md` - specialty food items and macros
- `src/data/rules.md` - hard constraints, allergies, and dislikes
- `src/data/meal-recipes.md` - reusable meal recipes
- `src/data/user_stats.csv` - optional personal metrics for TDEE calculation
- `src/state/state.json` - generated plans, grocery lists, inventory, and session state

If `user_stats.csv` is not present, the planner falls back to default stats.

## Confidence Scoring

LLM-assisted grocery parsing uses a normalized `0.0` to `1.0` confidence scale:

- `>= 0.7` - high confidence; auto-saved to inventory
- `0.4` to `0.699` - review confidence; presented for confirmation
- `< 0.4` - low confidence; requires manual macro entry and can be saved to `specialty-ingredients.md`

Example grocery output:

```text
| 2 lbs boneless chicken thighs | Chicken Thighs | 2 | lbs | Chicken thigh, ... | 0.86 high | auto |
```

## Inventory-Aware Meal Generation

When `grocery_inventory` is populated:

1. Meal candidates are ranked by how many inventory ingredients they use.
2. Perishable items such as protein, dairy, vegetables, and fruit receive extra weight.
3. The `grocery_list` becomes the supplemental list of ingredients still needed.
4. `inventory_usage` is recorded in state as `{used, unused, supplemental}`.

When no inventory exists, deterministic generation behavior remains unchanged.

## Saved Meals

Saved meals are reusable recipes with ingredients, macros, instructions, category, and tags.

When adding a meal with an ingredient not found in `specialty-ingredients.md` or `food.csv`, the tool prompts for macro data and appends the new ingredient to `specialty-ingredients.md`.

Example:

```bash
uv run main.py add \
  --name "Quinoa Bowl" \
  --ingredients "Quinoa, Spinach" \
  --macros "300|12|50|8" \
  --instructions "Cook quinoa;Add spinach" \
  --category Lunch
```

## Configuration

Edit these files to customize the planner:

- `src/data/food.csv` - standardized food database
- `src/data/specialty-ingredients.md` - specialty nutritional data
- `src/data/rules.md` - constraints, allergies, and dislikes
- `src/data/user_stats.csv` - optional personal stats
- `src/state/state.json` - generated state, modified automatically

## Development

Run tests:

```bash
uv run pytest tests/
```

Format and type check:

```bash
uv run black src/
uv run mypy src/
```

## Architecture Overview

### State Management

- Session state is persisted in `src/state/state.json`
- State includes profile, preferences, generated meals, grocery items, and inventory
- State is automatically updated after each operation

### Generation Pipeline

1. Calculate TDEE
2. Load preferences, foods, recipes, and rules
3. Generate meals
4. Build grocery list
5. Persist state

## Project Structure

```text
meal-planner/
|-- README.md
|-- IMPLEMENTATION_SUMMARY.md
|-- pyproject.toml
|-- requirements.txt
|-- LICENSE
|-- main.py
|-- src/
|   |-- api/
|   |   |-- main.py
|   |   `-- endpoints/
|   |-- data/
|   |   |-- food.csv
|   |   |-- specialty-ingredients.md
|   |   |-- meal-recipes.md
|   |   |-- rules.md
|   |   `-- user_stats.csv
|   |-- state/
|   |   `-- state.json
|   |-- tools/
|   |   |-- generate_plan.py
|   |   |-- calculate_tdee.py
|   |   |-- update_state.py
|   |   |-- confidence.py
|   |   |-- llm_agent.py
|   |   |-- food_processor.py
|   |   |-- grocery_inventory.py
|   |   `-- add_saved_meal.py
|   `-- server.py
|-- tests/
`-- plan/
```

## License

MIT
