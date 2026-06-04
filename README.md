# Food & Nutrition Intelligence: 7-Day Meal Planner

An AI-driven meal planning assistant integrated with a local MCP server that generates personalized 7-day meal plans, tracks nutritional intake, and manages automatic grocery lists.

## Features

- **User Feature A**: Generate 7-day meal plans aligned with user preferences and nutritional goals
- Track nutritional macros and caloric intake
- Manage grocery lists automatically
- Handle state persistence across sessions
- Web search integration for missing nutritional data

## Prerequisites

- [mise](https://mise.jdx.dev) — tool version manager
- [uv](https://docs.astral.sh/uv/) — extremely fast Python package and project manager
- Internet connection (optional, for web search functionality)

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

## Quick Start

### Feature A: Generate Initial 7-Day Meal Plan

1. Start the meal planner server using `uv run` (this automatically handles your virtual environment context):
```bash
uv run src/server.py
```

2. The server will initialize with your preferences from `src/data/`:
   - `foods.md` - Your food preferences and dietary restrictions
   - `macros.md` - Nutritional data and macro goals
   - `rules.md` - Hard constraints (allergies, dislikes)

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
- `--ingredients` — Comma-separated list (must exist in `foods.md`)
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

When adding a meal with an ingredient not yet in `foods.md`, the tool prompts for:

1. **Food properties** — Category, preparation method, notes
2. **Macro data** — Portion size, calories, protein, carbs, fat

The new ingredient is appended to both `foods.md` and `macros.md`, so subsequent meals can reference it without re-entry.

Example flow:

```bash
# First time using "Quinoa" — not yet in foods.md
uv run main.py add --name "Quinoa Bowl" --ingredients "Quinoa, Spinach" --macros "300|12|50|8" --instructions "Cook quinoa;Add spinach" --category Lunch

# The tool will prompt for Quinoa's food properties and macros,
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
│   │   ├── foods.md              # Preferred and disliked foods
│   │   ├── macros.md             # Nutritional macros and goals
│   │   └── rules.md              # Hard constraints and allergies
│   ├── state/                    # Session state management
│   │   └── state.json            # Dynamic session data
│   ├── tools/                    # Core logic modules
│   │   ├── generate_plan.py      # Meal plan generation
│   │   ├── calculate_tdee.py     # TDEE calculation
│   │   ├── update_state.py       # State persistence
│   │   └── search_web.py         # Web search wrapper
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

## Configuration

Edit the following files to customize your meal planner:

- **`src/data/foods.md`** - Add/remove food preferences and dietary habits
- **`src/data/macros.md`** - Update nutritional data and macro goals
- **`src/data/rules.md`** - Modify constraints (allergies, food dislikes)
- **`src/state/state.json`** - Session state (modified automatically)

## Development

Use `uv run` to execute development tools within your isolated environment:

```bash
# Run tests
uv run pytest tests/

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

### Web Search Integration
- Uses `search_web.py` to fill gaps in nutritional data
- Supports searching for calorie/macro information for custom foods

## License

MIT