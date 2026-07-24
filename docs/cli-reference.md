# CLI & Server Reference

This document covers the command-line and direct API server interfaces. Most users will use the [web frontend](../README.md) instead.

## Table of Contents

- [Interactive Meal Planner CLI](#interactive-meal-planner-cli)
- [Command CLI](#command-cli)
- [REST API Server](#rest-api-server)

## Interactive Meal Planner CLI

Run the prompt-based meal planner interface:

```bash
uv run src/server.py
```

Commands available in the interactive session:

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

## Command CLI

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

## REST API Server

Start the FastAPI server:

```bash
uv run uvicorn src.api.main:app
```

For development with automatic reload:

```bash
uv run uvicorn src.api.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive API docs are at `http://localhost:8000/docs`.

Authenticated endpoints require the `X-API-Key` header:

```bash
curl -H "X-API-Key: $MEAL_PLANNER_API_KEY" http://localhost:8000/state/
```
