# Food & Nutrition Intelligence: 7-Day Meal Planner

An AI-driven meal planning assistant integrated with a local MCP server that generates personalized 7-day meal plans, tracks nutritional intake, and manages automatic grocery lists.

## Features

- **User Feature A**: Generate 7-day meal plans aligned with user preferences and nutritional goals
- Track nutritional macros and caloric intake
- Manage grocery lists automatically
- Handle state persistence across sessions

## Prerequisites

- [mise](https://mise.jdx.dev) — tool version manager
- [uv](https://docs.astral.sh/uv/) — extremely fast Python package and project manager

## Installation

```bash
# Install the Python version specified in your mise configuration
mise install

# Create a virtual environment using uv
uv venv

# Install Python dependencies instantly with uv
uv pip install -r requirements.txt

# Note: If your pyproject.toml is fully configured for uv, you can alternatively just run `uv sync`
```

### API Key Setup (for API usage)

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env to set your API key
# For development, you can use: dev-key-change-in-production
# For production, use a strong randomly generated key
```

## Quick Start

### Feature A: Generate Initial 7-Day Meal Plan

1. Start the meal planner server using `uv run` (this automatically handles your virtual environment context):
```bash
uv run src/server.py
```

2. The server will initialize with your preferences and metrics from `src/data/`:
   - `food.csv` - Standardized food database
   - `specialty-ingredients.md` - Specialty food items and macros
   - `rules.md` - Hard constraints (allergies, dislikes)
   - `meal-recipes.md` - Reusable meal recipes
   - `user_stats.csv` - (Optional) Personal metrics (height, weight, age, gender) to calculate custom TDEE. Falls back to defaults (175cm, 70kg, 30yo, male) if not present.

3. Interact with the terminal prompt to:
   - Review your profile
   - Generate a 7-day meal plan
   - View nutritional summaries
   - Export meal plans or grocery lists

## Usage Examples

### Viewing Your Current Profile
```
>>> show_profile
```
Displays your nutritional goals, TDEE, and current preferences.

### Generating a New Meal Plan
```
>>> generate_plan
```
Creates a fresh 7-day meal plan based on current preferences.

### Viewing Grocery List
```
>>> show_groceries
```
Displays the consolidated grocery list for your 7-day plan.

## Saved Meals Feature

Manage a personal library of reusable meal recipes with automatic nutritional tracking and ingredient validation.

### Adding a New Meal

Save a meal with ingredients, macros, and instructions:

```bash
uv run main.py add \
  --name "Chicken & Rice Bowl" \
  --ingredients "Chicken Breast, White Rice, Broccoli" \
  --macros "450|35|50|12" \
  --instructions "Cook chicken in a pan;Cook rice in a pot;Steam broccoli;Combine everything" \
  --category "Dinner" \
  --tags "high_protein,quick"
```

- `--name` — Name of the meal (re-adding the same name updates the timestamp)
- `--ingredients` — Comma-separated list (must exist in `food.csv` or `specialty-ingredients.md`)
- `--macros` — Pipe-delimited: `calories|protein|carbs|fat`
- `--instructions` — Semicolon-separated steps
- `--category` — Meal category (default: `Dinner`)
- `--tags` — Comma-separated tags for filtering

### Listing Saved Meals

Display all saved meals in a compact table:

```bash
uv run main.py list
```

Filter by category or search by name:

```bash
uv run main.py list --category Breakfast
uv run main.py list --search "bowl"
```

Show full details with `--format verbose`:

```bash
uv run main.py list --format verbose
```

### Searching and Filtering Meals

Search with multiple criteria:

```bash
# Filter by category
uv run main.py search --category Lunch

# Filter by macro ranges
uv run main.py search --min-cal 300 --max-cal 600 --min-prot 20

# Filter by ingredient or tag
uv run main.py search --ingredient "Chicken Breast"
uv run mypy search --tag "high_protein"

# Combine multiple filters
uv run main.py search --category Dinner --min-cal 400 --tag "quick"
```

Supported search filters: `--category`, `--search`, `--min-cal`, `--max-cal`, `--min-prot`, `--max-prot`, `--min-carb`, `--max-carb`, `--min-fat`, `--max-fat`, `--ingredient`, `--tag`.

### Automatic Food Discovery

When adding a meal with an ingredient not yet in `specialty-ingredients.md` or `food.csv`, the tool prompts for:

1. **Macro data** — Portion size, calories, protein, carbs, fat

The new ingredient is appended to `specialty-ingredients.md`, so subsequent meals can reference it without re-entry.

Example flow:

```bash
# First time using "Quinoa" — not yet in specialty-ingredients.md
uv run main.py add --name "Quinoa Bowl" --ingredients "Quinoa, Spinach" --macros "300|12|50|8" --instructions "Cook quinoa;Add spinach" --category Lunch

# The tool will prompt for Quinoa's macros,
# then save both the new food and the meal.
```

## Project Structure

```text
meal-planner/
├── README.md                      # This file
├── IMPLEMENTATION_SUMMARY.md      # High-level implementation notes
├── pyproject.toml                 # Python project configuration
├── requirements.txt               # Python dependencies
├── LICENSE                        # MIT License
├── main.py                        # Entry point script
├── src/
│   ├── data/                     # User preference data
│   │   ├── food.csv              # Standardized food database
│   │   ├── specialty-ingredients.md # Specialty food items and macros
│   │   ├── meal-recipes.md       # Reusable meal recipes
│   │   ├── rules.md              # Hard constraints and allergies
│   │   └── user_stats.csv        # (Optional) Personal stats/metrics (ignored)
│   ├── state/                    # Session state management
│   │   └── state.json            # Dynamic session data
│   ├── tools/                    # Core logic modules
│   │   ├── generate_plan.py      # Meal plan generation
│   │   ├── calculate_tdee.py     # TDEE calculation
│   │   └── update_state.py       # State persistence
│   └── server.py                 # Server logic
├── tests/                        # Test suite
│   ├── conftest.py              # Test fixtures
│   ├── test_generation.py       # Plan generation tests
│   └── test_state_persistence.py # State persistence tests
└── plan/                        # Planning artifacts
    ├── plan.md                  # Main planning document
    ├── requirements.md          # Planning requirements
    ├── tasks.md                 # Task definitions
    └── init-prompt.md           # Initial prompt template
```

## API Server

The meal planner includes a RESTful API built with FastAPI for programmatic access.

### Starting the API Server

```bash
# Start the FastAPI server
uv run uvicorn src.api.main:app --reload
```

The server will be available at `http://localhost:8000` with interactive API documentation at `http://localhost:8000/docs`.

## Configuration

Edit the following files to customize your meal planner:

- **`src/data/food.csv`** - Standardized food database
- **`src/data/specialty-ingredients.md`** - Update specialty nutritional data
- **`src/data/rules.md`** - Modify constraints (allergies, food dislikes)
- **`src/data/user_stats.csv`** - (Optional) Custom physical stats/metrics (create to set personal metrics)
- **`src/state/state.json`** - Session state (modified automatically)

## Development

### Running Unit Tests

You can run the unit tests in the `tests/` folder using `pytest`:

**Option 1: Using `uv` (Recommended)**
```bash
uv run pytest tests/
```

**Option 2: Using the virtual environment directly**
```bash
# Activate the virtual environment (Windows)
.venv\Scripts\activate
pytest tests/

# Activate the virtual environment (macOS/Linux)
source .venv/bin/activate
pytest tests/
```

### Other Development Commands

Use `uv run` to execute other development tools:

```bash
# Format code
uv run black src/

# Type check
uv run mypy src/
```

## Architecture Overview

### State Management
- Session state is persisted in `src/state/state.json`
- Includes profile, preferences, generated meals, and grocery items
- State is automatically updated after each operation

### Generation Pipeline
1. **Calculate TDEE** → Determine caloric needs
2. **Load Preferences** → Read foods, macros, rules
3. **Generate Meals** → Create 7-day plan with nutritional balance
4. **Build Grocery List** → Consolidate ingredients
5. **Persist State** → Save to state.json

## License

MIT