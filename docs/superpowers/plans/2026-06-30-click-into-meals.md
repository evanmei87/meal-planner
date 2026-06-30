# Click Into Meals Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Meals-list rows clickable to open a meal detail (Dialog on the list + the existing `/meals/:name` page), showing macros as token tiles, a meal-level `servings` field, and richer step-by-step instructions.

**Architecture:** Backend consolidates three duplicated `meal-recipes.md` parsers into one shared `parse_recipe_row` helper that also reads a new `servings` column, then threads `servings` through the models and write path. Frontend factors the detail body into a shared `MealDetail` component rendered by both a responsive `MealDetailDialog` (opened from clickable list rows) and the kept `MealDetailPage`; macros render as token `StatTile`s + a CSS ratio bar — no charting library.

**Tech Stack:** FastAPI + Pydantic (Python, `uv`/`pytest`), React 18 + TypeScript + Vite, TanStack Query, shadcn/ui on the Base UI engine, Tailwind 4, Vitest + Testing Library + MSW.

**Spec:** [`docs/superpowers/specs/2026-06-30-click-into-meals-design.md`](../specs/2026-06-30-click-into-meals-design.md) · **Issue:** [#6](https://github.com/evanmei87/meal-planner/issues/6)

## Global Constraints

- **Nutrition is meal-level only.** `ingredients` stays `list[str]`. Per-ingredient macros/serving sizes are a separate follow-up issue (Task 11). Do not restructure ingredients.
- **New column order** for `meal-recipes.md`: `name | version | category | servings | macros | ingredients | instructions | tags` (8 columns). `servings` is an integer ≥ 1; macros stay `cal,prot,carb,fat`.
- **Displayed macros are per serving.** Do not recompute existing meal macros; existing 5 meals get `servings = 1` so their stored macros already equal one serving.
- **No new dependencies.** No charting library, no `vaul`. Macro UI is tokens + divs. Detail overlay is one responsive Dialog.
- **No `GET /meals/{name}` endpoint.** The Dialog uses the clicked row's already-loaded meal; the page keeps using the `useMeals()` list.
- **Intra-`src/tools` imports use the relative form** (`from .recipe_format import ...`), matching `food_processor.py`'s `from .confidence import ...`. This resolves under both the API (`src.tools` package) and pytest (`tools` package).
- **Backend commands:** `uv run pytest tests/ -q`, `uv run black src/`, `uv run mypy src/`. **Frontend (from `web/`):** `npm test -- --run`, `npx tsc --noEmit`.
- Commit after every task. Commit messages reference `#6`.

---

### Task 1: Shared recipe-row parser (`recipe_format.py`)

Create one parser that turns a markdown table row into a meal dict (incl. `servings`) and returns `None` for header/separator/blank/malformed rows. This replaces the three divergent parsers in Task 2.

**Files:**
- Create: `src/tools/recipe_format.py`
- Test: `tests/test_recipe_format.py`

**Interfaces:**
- Produces: `parse_recipe_row(line: str) -> dict | None`. On a data row returns keys: `name: str`, `version: str`, `category: str`, `servings: int`, `macros_raw: str`, `macros: dict` (`calories/protein/carbs/fat` ints), `ingredients: list[str]`, `instructions: list[str]`, `tags: list[str]`. Returns `None` for non-data rows.
- Produces: `RECIPE_COLUMN_COUNT = 8`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_recipe_format.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.recipe_format import parse_recipe_row, RECIPE_COLUMN_COUNT

DATA_ROW = (
    "| Chicken Bowl | 2024-01-01T00:00:00 | Dinner | 2 | 600,45,55,12 "
    "| Chicken Breast, White Rice | Cook chicken; Cook rice | high_protein, quick |"
)
HEADER_ROW = "| name | version | category | servings | macros | ingredients | instructions | tags |"
SEPARATOR_ROW = "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"


def test_column_count_is_eight():
    assert RECIPE_COLUMN_COUNT == 8


def test_parses_all_fields():
    meal = parse_recipe_row(DATA_ROW)
    assert meal['name'] == 'Chicken Bowl'
    assert meal['version'] == '2024-01-01T00:00:00'
    assert meal['category'] == 'Dinner'
    assert meal['servings'] == 2
    assert meal['macros'] == {'calories': 600, 'protein': 45, 'carbs': 55, 'fat': 12}
    assert meal['ingredients'] == ['Chicken Breast', 'White Rice']
    assert meal['instructions'] == ['Cook chicken', 'Cook rice']
    assert meal['tags'] == ['high_protein', 'quick']


def test_header_row_returns_none():
    assert parse_recipe_row(HEADER_ROW) is None


def test_separator_row_returns_none():
    assert parse_recipe_row(SEPARATOR_ROW) is None


def test_blank_or_nonrow_returns_none():
    assert parse_recipe_row("") is None
    assert parse_recipe_row("   ") is None
    assert parse_recipe_row("<!-- comment -->") is None


def test_empty_tags_cell_keeps_columns_aligned():
    row = "| Plain | v1 | Snack | 1 | 100,5,10,2 | Apple | Eat it | |"
    meal = parse_recipe_row(row)
    assert meal['name'] == 'Plain'
    assert meal['tags'] == []
    assert meal['servings'] == 1


def test_bad_servings_defaults_to_one():
    row = "| X | v1 | Snack | abc | 100,5,10,2 | Apple | Eat | snack |"
    assert parse_recipe_row(row)['servings'] == 1


def test_wrong_column_count_returns_none():
    assert parse_recipe_row("| only | three | cols |") is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_recipe_format.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'tools.recipe_format'`.

- [ ] **Step 3: Implement `recipe_format.py`**

Create `src/tools/recipe_format.py`:

```python
"""Shared parser for a single `meal-recipes.md` table row.

Column order: name | version | category | servings | macros | ingredients | instructions | tags
"""

RECIPE_COLUMN_COUNT = 8


def _split_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith('|'):
        stripped = stripped[1:]
    if stripped.endswith('|'):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split('|')]


def _is_separator(cells: list[str]) -> bool:
    return all(cell and set(cell) <= set(':-') for cell in cells)


def _parse_macros(raw: str) -> dict:
    parts = raw.split(',')

    def value(index: int) -> int:
        return int(parts[index]) if len(parts) > index and parts[index].strip() else 0

    try:
        return {
            'calories': value(0),
            'protein': value(1),
            'carbs': value(2),
            'fat': value(3),
        }
    except ValueError:
        return {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}


def _parse_servings(raw: str) -> int:
    try:
        servings = int(raw)
    except (ValueError, TypeError):
        return 1
    return servings if servings >= 1 else 1


def parse_recipe_row(line: str) -> dict | None:
    """Parse one markdown table row into a meal dict, or None if not a data row."""
    if not line.strip().startswith('|'):
        return None

    cells = _split_row(line)
    if len(cells) != RECIPE_COLUMN_COUNT:
        return None
    if _is_separator(cells):
        return None
    if cells[0].lower() == 'name':  # header row
        return None

    macros_raw = cells[4]
    return {
        'name': cells[0],
        'version': cells[1],
        'category': cells[2],
        'servings': _parse_servings(cells[3]),
        'macros_raw': macros_raw,
        'macros': _parse_macros(macros_raw),
        'ingredients': [item.strip() for item in cells[5].split(',') if item.strip()],
        'instructions': [step.strip() for step in cells[6].split(';') if step.strip()],
        'tags': [tag.strip() for tag in cells[7].split(',') if tag.strip()],
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_recipe_format.py -q`
Expected: PASS (8 tests).

- [ ] **Step 5: Commit**

```bash
git add src/tools/recipe_format.py tests/test_recipe_format.py
git commit -m "feat: add shared meal-recipes row parser with servings (#6)"
```

---

### Task 2: Route all three parsers through the shared helper

Replace the duplicated row parsing in `load_saved_meals.py`, `search_meals.py`, and `add_saved_meal.py` with `parse_recipe_row`, and update the three test fixtures to the 8-column format.

**Files:**
- Modify: `src/tools/load_saved_meals.py` (the `load_saved_meals` loop)
- Modify: `src/tools/search_meals.py` (its local `load_saved_meals` loop)
- Modify: `src/tools/add_saved_meal.py:load_recipes`
- Test: `tests/test_load_saved_meals.py`, `tests/test_search_meals.py`, `tests/test_add_saved_meal.py` (fixtures)

**Interfaces:**
- Consumes: `parse_recipe_row` (Task 1).
- Produces: meal dicts from all three loaders now include `servings: int`.

- [ ] **Step 1: Update test fixtures to the 8-column format (failing)**

In `tests/test_load_saved_meals.py`, replace `RECIPES_CONTENT` with:

```python
RECIPES_CONTENT = """\
<!-- meal-recipes.md -->
<!-- name | version | category | servings | macros(cal,prot,carb,fat) | ingredients | instructions | tags -->

| name | version | category | servings | macros | ingredients | instructions | tags |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Chicken Bowl | 2024-01-01T00:00:00 | Dinner | 1 | 600,45,55,12 | Chicken Breast, White Rice, Broccoli | Cook chicken;Cook rice;Steam broccoli | high_protein,quick |
| Oatmeal | 2024-01-02T00:00:00 | Breakfast | 1 | 400,15,70,8 | Oatmeal, Berries | Cook oatmeal;Add berries | vegetarian |
| Salmon Bowl | 2024-01-03T00:00:00 | Dinner | 2 | 700,50,45,25 | Salmon, Quinoa, Spinach | Cook salmon;Cook quinoa | high_protein |
"""
```

Add one assertion to `test_load_saved_meals_parses_fields` (after the existing asserts):

```python
    assert chicken['servings'] == 1
```

In `tests/test_add_saved_meal.py`, replace the `RECIPES_MD_HEADER` and `MEAL_ROW` constants with:

```python
RECIPES_MD_HEADER = """\
<!-- meal-recipes.md -->
<!-- name | version | category | servings | macros(cal,prot,carb,fat) | ingredients | instructions | tags -->

| name | version | category | servings | macros | ingredients | instructions | tags |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
"""

MEAL_ROW = "| Chicken Bowl | 2024-01-01T00:00:00 | Dinner | 1 | 500,40,50,10 | Chicken Breast, White Rice | Cook chicken;Cook rice | high_protein |"
```

Add to `test_load_recipes_parses_row` (after existing asserts):

```python
    assert meals[0]['servings'] == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_load_saved_meals.py tests/test_add_saved_meal.py -q`
Expected: FAIL — current parsers don't read `servings` / mis-handle the new column count, so `servings`/field assertions fail.

- [ ] **Step 3: Rewrite the three loaders to use `parse_recipe_row`**

In `src/tools/load_saved_meals.py`, add the import at the top (after the existing `from pathlib import Path`):

```python
from .recipe_format import parse_recipe_row
```

Replace the parsing block (the `lines = ...`, `data_start_idx`, and the `for line in lines[data_start_idx:]:` loop through `meals.append(meal)`) with:

```python
    for line in recipes_content.strip().split('\n'):
        meal = parse_recipe_row(line)
        if meal is not None:
            meals.append(meal)
```

Leave the `if not recipes_content.strip(): return meals` guard and the filter/search blocks below unchanged.

In `src/tools/search_meals.py`, add at the top:

```python
from .recipe_format import parse_recipe_row
```

Replace its local `load_saved_meals` parsing block (everything from `lines = recipes_content.strip().split('\n')` through the `meals.append(meal)` / macro-parsing block) with the same loop:

```python
    for line in recipes_content.strip().split('\n'):
        meal = parse_recipe_row(line)
        if meal is not None:
            meals.append(meal)
```

In `src/tools/add_saved_meal.py`, add at the top (after `from pathlib import Path`):

```python
from .recipe_format import parse_recipe_row
```

Replace the body of `load_recipes` with:

```python
def load_recipes(recipes_content: str) -> list:
    """Parse recipes markdown content and return list of meal dicts."""
    if not recipes_content.strip():
        return []
    meals = []
    for line in recipes_content.strip().split('\n'):
        meal = parse_recipe_row(line)
        if meal is not None:
            meals.append(meal)
    return meals
```

- [ ] **Step 4: Run the full backend suite to verify pass**

Run: `uv run pytest tests/ -q`
Expected: PASS. (`test_search_meals.py` monkeypatches `load_saved_meals` with dict lists, so it is unaffected; confirm it stays green.)

- [ ] **Step 5: Commit**

```bash
git add src/tools/load_saved_meals.py src/tools/search_meals.py src/tools/add_saved_meal.py tests/test_load_saved_meals.py tests/test_add_saved_meal.py
git commit -m "refactor: route all meal-recipes parsers through shared row parser (#6)"
```

---

### Task 3: Thread `servings` through models, write path, and endpoint

Add `servings` to the API models, write it when appending a meal row, and pass it from the add-meal endpoint.

**Files:**
- Modify: `src/api/models.py` (`MealResponse`, `AddMealRequest`)
- Modify: `src/tools/add_saved_meal.py` (`add_saved_meal`, `add_saved_meal_from_request`)
- Test: `tests/test_add_saved_meal.py`, `tests/test_api/test_meals.py`

**Interfaces:**
- Consumes: shared parser (Task 1/2).
- Produces: `MealResponse.servings: int` (default 1), `AddMealRequest.servings: int` (default 1); `add_saved_meal(..., servings: int = 1)` writes the 8-column row; `add_saved_meal_from_request` reads `meal_data['servings']`.

- [ ] **Step 1: Write failing tests**

Add to `tests/test_add_saved_meal.py`:

```python
from tools.add_saved_meal import add_saved_meal_from_request, load_recipes


def test_add_meal_writes_servings_column(tmp_path, monkeypatch):
    import tools.add_saved_meal as asm

    recipes_path = tmp_path / "meal-recipes.md"
    recipes_path.write_text(RECIPES_MD_HEADER)
    specialty_path = tmp_path / "specialty-ingredients.md"
    specialty_path.write_text(SPECIALTY_MD)

    monkeypatch.setattr(asm, 'load_static_data', lambda: {
        'food_db': '', 'specialty': SPECIALTY_MD, 'recipes': recipes_path.read_text(),
    })
    monkeypatch.setattr(asm.Path, 'write_text', Path.write_text)  # keep real write
    monkeypatch.setattr(
        asm, 'save_recipes',
        lambda content, _path: bool(recipes_path.write_text(content)) or True,
    )

    result = add_saved_meal_from_request({
        'name': 'Test Bowl',
        'ingredients': ['Chicken Breast'],
        'macros': {'calories': 400, 'protein': 30, 'carbs': 20, 'fat': 10},
        'instructions': ['Cook it', 'Plate it'],
        'category': 'Dinner',
        'tags': ['quick'],
        'servings': 3,
    }, prompt_session=False)

    assert result['success'] is True
    meals = load_recipes(recipes_path.read_text())
    saved = next(m for m in meals if m['name'] == 'Test Bowl')
    assert saved['servings'] == 3
    assert saved['instructions'] == ['Cook it', 'Plate it']


def test_add_meal_defaults_servings_to_one(tmp_path, monkeypatch):
    import tools.add_saved_meal as asm
    recipes_path = tmp_path / "meal-recipes.md"
    recipes_path.write_text(RECIPES_MD_HEADER)
    monkeypatch.setattr(asm, 'load_static_data', lambda: {
        'food_db': '', 'specialty': SPECIALTY_MD, 'recipes': recipes_path.read_text(),
    })
    monkeypatch.setattr(
        asm, 'save_recipes',
        lambda content, _path: bool(recipes_path.write_text(content)) or True,
    )
    add_saved_meal_from_request({
        'name': 'No Servings Meal',
        'ingredients': ['Chicken Breast'],
        'macros': {'calories': 400, 'protein': 30, 'carbs': 20, 'fat': 10},
        'instructions': ['Cook'],
        'category': 'Dinner',
        'tags': [],
    }, prompt_session=False)
    meals = load_recipes(recipes_path.read_text())
    saved = next(m for m in meals if m['name'] == 'No Servings Meal')
    assert saved['servings'] == 1
```

Add to `tests/test_api/test_meals.py`:

```python
def test_meal_response_defaults_servings(client, api_key_headers, sample_meal):
    """A meal dict without 'servings' serializes with servings defaulted to 1."""
    with patch('src.api.endpoints.meals.load_saved_meals') as mock_load:
        mock_load.return_value = [sample_meal]  # sample_meal has no 'servings'
        response = client.get("/meals/", headers=api_key_headers)
        assert response.status_code == 200
        assert response.json()[0]['servings'] == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_add_saved_meal.py tests/test_api/test_meals.py -q`
Expected: FAIL — `add_saved_meal` has no `servings` param / row lacks the column; `MealResponse` has no `servings` field.

- [ ] **Step 3: Add `servings` to the models**

In `src/api/models.py`, in `class AddMealRequest`, add after the `category` field:

```python
    servings: int = Field(default=1, ge=1, description="Number of servings the recipe yields")
```

In `class MealResponse`, add after the `category` field:

```python
    servings: int = Field(default=1, ge=1)
```

- [ ] **Step 4: Write `servings` in the add path**

In `src/tools/add_saved_meal.py`, change the `add_saved_meal` signature to add `servings`:

```python
def add_saved_meal(meal_name: str, ingredients: list,
                   macros: dict, instructions: list,
                   category: str = "Dinner", tags: list = None,
                   servings: int = 1,
                   prompt_session=True) -> dict:
```

Replace the `new_row = ...` line with the 8-column row (note the new `servings` cell after `category`):

```python
    new_row = f"| {meal_name} | {timestamp} | {category} | {servings} | {macros_str} | {ingredients_str} | {instructions_str} | {tags_formatted} |"
```

In `add_saved_meal_from_request`, pass `servings` through:

```python
    return add_saved_meal(
        meal_name=meal_data.get('name', ''),
        ingredients=meal_data.get('ingredients', []),
        macros=meal_data.get('macros', {}),
        instructions=meal_data.get('instructions', []),
        category=meal_data.get('category', 'Dinner'),
        tags=meal_data.get('tags', []),
        servings=meal_data.get('servings', 1),
        prompt_session=prompt_session,
    )
```

In `src/api/endpoints/meals.py`, in `add_meal`, add `servings` to the `meal_data` dict:

```python
        meal_data = {
            'name': request.name,
            'ingredients': request.ingredients,
            'macros': request.macros,
            'instructions': request.instructions,
            'category': request.category,
            'tags': request.tags,
            'servings': request.servings,
        }
```

- [ ] **Step 5: Run tests to verify pass**

Run: `uv run pytest tests/test_add_saved_meal.py tests/test_api/test_meals.py -q`
Expected: PASS.

- [ ] **Step 6: Full suite + type/format check**

Run: `uv run pytest tests/ -q && uv run black src/ && uv run mypy src/`
Expected: tests PASS; black formats; mypy clean (or no new errors).

- [ ] **Step 7: Commit**

```bash
git add src/api/models.py src/tools/add_saved_meal.py src/api/endpoints/meals.py tests/test_add_saved_meal.py tests/test_api/test_meals.py
git commit -m "feat: thread meal-level servings through models and add path (#6)"
```

---

### Task 4: Enrich the five existing recipes (servings + step-by-step instructions)

Migrate `meal-recipes.md` to the 8-column format, set `servings = 1` for all five (macros already represent one serving), and expand each one-line instruction into real `;`-separated steps.

**Files:**
- Modify: `src/data/meal-recipes.md`
- Test: `tests/test_meal_recipes_data.py`

**Interfaces:**
- Consumes: `load_saved_meals` (reads the real file unpatched).

- [ ] **Step 1: Write the failing data-integrity test**

Create `tests/test_meal_recipes_data.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.load_saved_meals import load_saved_meals


def test_all_recipes_have_servings_and_multistep_instructions():
    meals = load_saved_meals()
    assert len(meals) == 5
    for meal in meals:
        assert meal['servings'] >= 1, f"{meal['name']} missing servings"
        assert len(meal['instructions']) >= 3, (
            f"{meal['name']} should have step-by-step instructions"
        )
        assert meal['macros']['calories'] > 0


def test_known_meal_still_loads():
    meals = load_saved_meals()
    names = {m['name'] for m in meals}
    assert 'Salmon & Quinoa' in names
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_meal_recipes_data.py -q`
Expected: FAIL — current file has single-step instructions and no `servings` column (parser returns 7-cell rows → `None` → `len(meals) == 0`).

- [ ] **Step 3: Rewrite `src/data/meal-recipes.md`**

Replace the entire file with (header comment documents the new column):

```markdown
# Meal Recipes Storage
# Format: Markdown Table
# Columns: name|version|category|servings|macros (cal,prot,carb,fat)|ingredients|instructions|tags

| name | version | category | servings | macros | ingredients | instructions | tags |
|:---:|:---:|:---:|:---:|:---|:---:|:---:|:---:|
| Chicken & Rice Bowl | 2026-06-03T00:00:00 | Dinner | 1 | 650,45,55,8 | Chicken Thighs, White Rice, Broccoli | Season chicken thighs with salt and pepper; Sear in a hot pan 6-7 min per side until cooked through; Cook white rice per package directions; Steam broccoli 4-5 min until tender; Slice chicken and serve over rice with broccoli | grilled,steamed,roasted,comfort,high_protein |
| Oatmeal Breakfast | 2026-06-03T00:00:00 | Breakfast | 1 | 320,23,28,3 | Oatmeal, Orgain Plant Protein, Cherry Tomatoes | Bring water to a boil and add oatmeal; Simmer 4-5 min, stirring, until thick; Remove from heat and stir in the protein powder; Halve the cherry tomatoes; Top the oatmeal with tomatoes and serve | high_protein |
| Greek Yogurt Bowl | 2026-06-03T00:00:00 | Lunch | 1 | 180,22,7,9 | Greek Yogurt, Bell Peppers, Cucumber | Spoon Greek yogurt into a bowl; Thinly slice the bell peppers; Dice the cucumber; Layer peppers and cucumber over the yogurt and serve | probiotic |
| Salmon & Quinoa | 2026-06-03T00:00:00 | Dinner | 1 | 520,30,18,45 | Salmon, Quinoa, Spinach, Bell Peppers | Rinse quinoa and cook in water 15 min until fluffy; Season salmon with lemon, salt and pepper; Bake salmon at 200C/400F for 12-15 min; Saute spinach and sliced bell peppers 3-4 min; Plate salmon over quinoa with the vegetables | omega_3,lean |
| Tofu Stir-fry | 2026-06-03T00:00:00 | Dinner | 1 | 380,25,32,10 | Tofu, Brown Rice, Broccoli, Bell Peppers, Mushrooms | Cook brown rice per package directions; Press and cube the tofu; Pan-fry tofu until golden on all sides; Add broccoli, bell peppers and mushrooms and stir-fry 4-5 min; Serve the tofu and vegetables over the rice | plant_based,vegan |
```

- [ ] **Step 4: Run the data test + full suite**

Run: `uv run pytest tests/test_meal_recipes_data.py tests/ -q`
Expected: PASS (the real-file test and all existing tests).

- [ ] **Step 5: Commit**

```bash
git add src/data/meal-recipes.md tests/test_meal_recipes_data.py
git commit -m "feat: enrich recipes with servings and step-by-step instructions (#6)"
```

---

### Task 5: Add a responsive `Dialog` primitive

Add a shadcn-style Dialog wrapper over the Base UI dialog primitive (already installed at `@base-ui/react/dialog`), styled as a centered modal on `sm+` and a bottom sheet on mobile.

**Files:**
- Create: `web/src/components/ui/dialog.tsx`
- Test: `web/src/components/ui/dialog.test.tsx`

**Interfaces:**
- Produces: `Dialog`, `DialogTrigger`, `DialogContent`, `DialogTitle`, `DialogDescription`, `DialogClose` from `@/components/ui/dialog`.

> **Preferred route:** run `cd web && npx shadcn add dialog` to generate the version-matched Base UI dialog, then adapt `DialogContent` with the responsive classes from Step 3 and confirm the exports above. If the CLI cannot run (offline), author the file by hand using Step 3 verbatim. Either way, the test in Step 1 defines the contract.

- [ ] **Step 1: Write the failing test**

Create `web/src/components/ui/dialog.test.tsx`:

```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogTitle,
} from '@/components/ui/dialog'

describe('Dialog', () => {
  it('opens content when the trigger is clicked', () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>Hello</DialogTitle>
        </DialogContent>
      </Dialog>
    )
    expect(screen.queryByText('Hello')).not.toBeInTheDocument()
    fireEvent.click(screen.getByText('Open'))
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run to verify failure**

Run: `cd web && npm test -- --run src/components/ui/dialog.test.tsx`
Expected: FAIL — `Failed to resolve import "@/components/ui/dialog"`.

- [ ] **Step 3: Create `dialog.tsx`**

Create `web/src/components/ui/dialog.tsx`:

```tsx
import { Dialog as DialogPrimitive } from "@base-ui/react/dialog"

import { cn } from "@/lib/utils"

function Dialog(props: DialogPrimitive.Root.Props) {
  return <DialogPrimitive.Root {...props} />
}

function DialogTrigger(props: DialogPrimitive.Trigger.Props) {
  return <DialogPrimitive.Trigger data-slot="dialog-trigger" {...props} />
}

function DialogClose(props: DialogPrimitive.Close.Props) {
  return <DialogPrimitive.Close data-slot="dialog-close" {...props} />
}

function DialogContent({
  className,
  children,
  ...props
}: DialogPrimitive.Popup.Props) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Backdrop className="fixed inset-0 z-50 bg-black/50 transition-opacity data-[ending-style]:opacity-0 data-[starting-style]:opacity-0" />
      <DialogPrimitive.Popup
        data-slot="dialog-content"
        className={cn(
          "fixed z-50 grid gap-4 overflow-y-auto bg-card text-card-foreground shadow-lg outline-none",
          // mobile: bottom sheet
          "inset-x-0 bottom-0 max-h-[85vh] rounded-t-xl border-t border-border p-4",
          // sm+: centered modal
          "sm:inset-auto sm:top-1/2 sm:left-1/2 sm:bottom-auto sm:max-h-[85vh] sm:w-full sm:max-w-lg sm:-translate-x-1/2 sm:-translate-y-1/2 sm:rounded-xl sm:border sm:p-6",
          className
        )}
        {...props}
      >
        {children}
      </DialogPrimitive.Popup>
    </DialogPrimitive.Portal>
  )
}

function DialogTitle({ className, ...props }: DialogPrimitive.Title.Props) {
  return (
    <DialogPrimitive.Title
      data-slot="dialog-title"
      className={cn("text-lg font-semibold", className)}
      {...props}
    />
  )
}

function DialogDescription({
  className,
  ...props
}: DialogPrimitive.Description.Props) {
  return (
    <DialogPrimitive.Description
      data-slot="dialog-description"
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  )
}

export {
  Dialog,
  DialogTrigger,
  DialogClose,
  DialogContent,
  DialogTitle,
  DialogDescription,
}
```

> If `npx shadcn add dialog` was used and its prop type names differ (e.g. namespaced `Dialog.Root.Props`), keep the generated types and only port the responsive `className` on `DialogContent`. The exported names must match Step 1.

- [ ] **Step 4: Run to verify pass + type check**

Run: `cd web && npm test -- --run src/components/ui/dialog.test.tsx && npx tsc --noEmit`
Expected: PASS; no type errors.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/ui/dialog.tsx web/src/components/ui/dialog.test.tsx
git commit -m "feat(web): add responsive Dialog primitive on Base UI (#6)"
```

---

### Task 6: Macro display components (`StatTile` + `MacroBar`)

Build the token-styled macro tiles and the CSS protein/carbs/fat ratio bar. These are meal-specific, so they live under `features/meals`.

**Files:**
- Create: `web/src/features/meals/MacroDisplay.tsx`
- Test: `web/src/features/meals/MacroDisplay.test.tsx`

**Interfaces:**
- Produces: `StatTile({ label: string, value: string })` and `MacroBar({ protein: number, carbs: number, fat: number })` from `@/features/meals/MacroDisplay`.

- [ ] **Step 1: Write the failing test**

Create `web/src/features/meals/MacroDisplay.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatTile, MacroBar } from '@/features/meals/MacroDisplay'

describe('StatTile', () => {
  it('renders a label and value', () => {
    render(<StatTile label="Calories" value="650" />)
    expect(screen.getByText('Calories')).toBeInTheDocument()
    expect(screen.getByText('650')).toBeInTheDocument()
  })
})

describe('MacroBar', () => {
  it('renders three labelled segments sized by gram proportion', () => {
    render(<MacroBar protein={50} carbs={30} fat={20} />)
    const bar = screen.getByRole('img', { name: /protein 50g.*carbs 30g.*fat 20g/i })
    expect(bar).toBeInTheDocument()
    const protein = screen.getByTestId('macro-segment-protein')
    expect(protein).toHaveStyle({ width: '50%' })
  })

  it('renders nothing meaningful when all macros are zero', () => {
    render(<MacroBar protein={0} carbs={0} fat={0} />)
    expect(screen.getByTestId('macro-segment-protein')).toHaveStyle({ width: '0%' })
  })
})
```

- [ ] **Step 2: Run to verify failure**

Run: `cd web && npm test -- --run src/features/meals/MacroDisplay.test.tsx`
Expected: FAIL — `Failed to resolve import "@/features/meals/MacroDisplay"`.

- [ ] **Step 3: Implement `MacroDisplay.tsx`**

Create `web/src/features/meals/MacroDisplay.tsx`:

```tsx
export function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-muted/40 px-3 py-2 text-center">
      <div className="text-lg font-semibold text-foreground">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  )
}

interface MacroBarProps {
  protein: number
  carbs: number
  fat: number
}

export function MacroBar({ protein, carbs, fat }: MacroBarProps) {
  const total = protein + carbs + fat
  const pct = (grams: number) => (total > 0 ? (grams / total) * 100 : 0)

  const segments = [
    { key: 'protein', grams: protein, color: 'bg-chart-1' },
    { key: 'carbs', grams: carbs, color: 'bg-chart-3' },
    { key: 'fat', grams: fat, color: 'bg-chart-5' },
  ] as const

  const label = `Protein ${protein}g, Carbs ${carbs}g, Fat ${fat}g`

  return (
    <div>
      <div
        role="img"
        aria-label={label}
        className="flex h-2.5 w-full overflow-hidden rounded-full bg-muted"
      >
        {segments.map((segment) => (
          <div
            key={segment.key}
            data-testid={`macro-segment-${segment.key}`}
            className={segment.color}
            style={{ width: `${pct(segment.grams)}%` }}
          />
        ))}
      </div>
      <div className="mt-1 flex gap-3 text-xs text-muted-foreground">
        {segments.map((segment) => (
          <span key={segment.key} className="flex items-center gap-1 capitalize">
            <span className={`inline-block h-2 w-2 rounded-full ${segment.color}`} />
            {segment.key} {segment.grams}g
          </span>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run to verify pass**

Run: `cd web && npm test -- --run src/features/meals/MacroDisplay.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/features/meals/MacroDisplay.tsx web/src/features/meals/MacroDisplay.test.tsx
git commit -m "feat(web): add macro stat tiles and ratio bar (#6)"
```

---

### Task 7: Shared `MealDetail` component + refactor `MealDetailPage`

Extract the saved-meal detail body into a reusable `MealDetail` that shows servings, the per-serving macro section, ingredients, numbered steps, and tags. Point the existing page at it.

**Files:**
- Create: `web/src/features/meals/MealDetail.tsx`
- Create: `web/src/features/meals/MealDetail.test.tsx`
- Modify: `web/src/api/types.ts` (`MealResponse.servings`)
- Modify: `web/src/features/meals/MealDetailPage.tsx` (saved-meal branch)
- Modify: `web/src/features/meals/MealDetailPage.test.tsx` (`SAVED_MEAL` gains `servings`)

**Interfaces:**
- Consumes: `StatTile`, `MacroBar` (Task 6); `MealResponse` type.
- Produces: `MealDetail({ meal: MealResponse })` from `@/features/meals/MealDetail`.

- [ ] **Step 1: Add `servings` to the `MealResponse` type**

In `web/src/api/types.ts`, in `interface MealResponse`, add after `category`:

```ts
  servings: number
```

- [ ] **Step 2: Write the failing test**

Create `web/src/features/meals/MealDetail.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MealDetail } from '@/features/meals/MealDetail'
import type { MealResponse } from '@/api/types'

const MEAL: MealResponse = {
  name: 'Chicken Bowl',
  version: '2024-01-01',
  category: 'Dinner',
  servings: 2,
  macros: { calories: 650, protein: 45, carbs: 55, fat: 8 },
  ingredients: ['Chicken', 'Rice'],
  instructions: ['Season chicken', 'Sear chicken', 'Serve over rice'],
  tags: ['high_protein'],
}

describe('MealDetail', () => {
  it('renders name, servings, macros, ingredients, and numbered steps', () => {
    render(<MealDetail meal={MEAL} />)
    expect(screen.getByText('Chicken Bowl')).toBeInTheDocument()
    expect(screen.getByText(/makes 2 servings/i)).toBeInTheDocument()
    expect(screen.getByText('650')).toBeInTheDocument()
    expect(screen.getByText('Season chicken')).toBeInTheDocument()
    expect(screen.getByText('Chicken')).toBeInTheDocument()
    expect(screen.getByText('high_protein')).toBeInTheDocument()
  })

  it('uses singular "serving" when servings is 1', () => {
    render(<MealDetail meal={{ ...MEAL, servings: 1 }} />)
    expect(screen.getByText(/makes 1 serving$/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 3: Run to verify failure**

Run: `cd web && npm test -- --run src/features/meals/MealDetail.test.tsx`
Expected: FAIL — `Failed to resolve import "@/features/meals/MealDetail"`.

- [ ] **Step 4: Implement `MealDetail.tsx`**

Create `web/src/features/meals/MealDetail.tsx`:

```tsx
import { Card } from '@/components/Card'
import type { MealResponse } from '@/api/types'
import { StatTile, MacroBar } from '@/features/meals/MacroDisplay'

export function MealDetail({ meal }: { meal: MealResponse }) {
  const servingLabel = `Makes ${meal.servings} serving${meal.servings === 1 ? '' : 's'}`

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">{meal.name}</h1>
      <p className="text-sm text-muted-foreground mb-1">{meal.category}</p>
      <p className="text-sm text-muted-foreground mb-4">{servingLabel}</p>

      <div className="mb-4">
        <p className="text-xs uppercase tracking-wide text-muted-foreground mb-2">
          Per serving
        </p>
        <div className="grid grid-cols-4 gap-2 mb-3">
          <StatTile label="Calories" value={String(meal.macros.calories)} />
          <StatTile label="Protein" value={`${meal.macros.protein}g`} />
          <StatTile label="Carbs" value={`${meal.macros.carbs}g`} />
          <StatTile label="Fat" value={`${meal.macros.fat}g`} />
        </div>
        <MacroBar
          protein={meal.macros.protein}
          carbs={meal.macros.carbs}
          fat={meal.macros.fat}
        />
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <h2 className="font-semibold mb-2">Ingredients</h2>
          <ul className="list-disc pl-5 text-sm text-foreground space-y-1">
            {meal.ingredients.map((ingredient) => (
              <li key={ingredient}>{ingredient}</li>
            ))}
          </ul>
        </Card>
        <Card>
          <h2 className="font-semibold mb-2">Instructions</h2>
          <ol className="list-decimal pl-5 text-sm text-foreground space-y-1">
            {meal.instructions.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
        </Card>
      </div>

      {meal.tags.length > 0 && (
        <div className="mt-4 flex gap-2 flex-wrap">
          {meal.tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 bg-muted text-muted-foreground text-xs rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Point `MealDetailPage` at `MealDetail`**

In `web/src/features/meals/MealDetailPage.tsx`, add the import:

```tsx
import { MealDetail } from '@/features/meals/MealDetail'
```

Replace the entire `if (savedMeal) { return ( ... ) }` block with:

```tsx
  if (savedMeal) {
    return <MealDetail meal={savedMeal} />
  }
```

The `planMeal` and not-found branches stay unchanged.

In `web/src/features/meals/MealDetailPage.test.tsx`, add `servings: 1,` to the `SAVED_MEAL` object (after `category`).

- [ ] **Step 6: Run the meals tests + type check**

Run: `cd web && npm test -- --run src/features/meals && npx tsc --noEmit`
Expected: PASS (`MealDetail.test`, `MealDetailPage.test`); no type errors.

- [ ] **Step 7: Commit**

```bash
git add web/src/api/types.ts web/src/features/meals/MealDetail.tsx web/src/features/meals/MealDetail.test.tsx web/src/features/meals/MealDetailPage.tsx web/src/features/meals/MealDetailPage.test.tsx
git commit -m "feat(web): shared MealDetail with servings and macro tiles (#6)"
```

---

### Task 8: Add optional `onRowClick` to the shared `Table`

Extend the shared `Table` so rows can be activated by mouse and keyboard, without changing existing call sites.

**Files:**
- Modify: `web/src/components/Table.tsx`
- Test: `web/src/components/Table.test.tsx`

**Interfaces:**
- Produces: `Table` accepts optional `onRowClick?: (row: Record<string, unknown>) => void`. When provided, each row is keyboard-focusable and activates on click / Enter / Space.

- [ ] **Step 1: Write the failing test**

Add to `web/src/components/Table.test.tsx`:

```tsx
import { fireEvent } from '@testing-library/react'

it('calls onRowClick when a row is clicked', () => {
  const onRowClick = vi.fn()
  render(
    <Table
      columns={[{ key: 'name', header: 'Name' }]}
      rows={[{ name: 'Alpha' }]}
      onRowClick={onRowClick}
    />
  )
  fireEvent.click(screen.getByText('Alpha'))
  expect(onRowClick).toHaveBeenCalledWith({ name: 'Alpha' })
})

it('activates a row on Enter key', () => {
  const onRowClick = vi.fn()
  render(
    <Table
      columns={[{ key: 'name', header: 'Name' }]}
      rows={[{ name: 'Alpha' }]}
      onRowClick={onRowClick}
    />
  )
  fireEvent.keyDown(screen.getByText('Alpha').closest('tr')!, { key: 'Enter' })
  expect(onRowClick).toHaveBeenCalledWith({ name: 'Alpha' })
})
```

Ensure `vi`, `render`, `screen` are imported in this file (add to the existing import from `vitest`/`@testing-library/react` if missing).

- [ ] **Step 2: Run to verify failure**

Run: `cd web && npm test -- --run src/components/Table.test.tsx`
Expected: FAIL — `onRowClick` is not a prop; handler never called.

- [ ] **Step 3: Implement `onRowClick`**

In `web/src/components/Table.tsx`, extend `TableProps`:

```tsx
interface TableProps {
  columns: Column[]
  rows: Record<string, unknown>[]
  onRowClick?: (row: Record<string, unknown>) => void
}
```

Change the function signature to `export function Table({ columns, rows, onRowClick }: TableProps) {` and replace the data-row `<tr>` with a click/keyboard-aware version:

```tsx
          {rows.map((row, i) => (
            <tr
              key={i}
              className={`border-t border-border hover:bg-muted/50 ${
                onRowClick ? 'cursor-pointer' : ''
              }`}
              {...(onRowClick
                ? {
                    role: 'button',
                    tabIndex: 0,
                    onClick: () => onRowClick(row),
                    onKeyDown: (e: React.KeyboardEvent) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        onRowClick(row)
                      }
                    },
                  }
                : {})}
            >
              {columns.map((col, colIndex) => (
                <td key={`${col.key}-${colIndex}`} className="px-3 py-2 text-foreground">
                  {col.render
                    ? col.render(row[col.key], row)
                    : String(row[col.key] ?? '')}
                </td>
              ))}
            </tr>
          ))}
```

- [ ] **Step 4: Run to verify pass**

Run: `cd web && npm test -- --run src/components/Table.test.tsx`
Expected: PASS (new + existing Table tests).

- [ ] **Step 5: Commit**

```bash
git add web/src/components/Table.tsx web/src/components/Table.test.tsx
git commit -m "feat(web): add optional keyboard-accessible onRowClick to Table (#6)"
```

---

### Task 9: `MealDetailDialog` + clickable Meals rows

Open the meal detail in the responsive Dialog when a Meals-list row is clicked, reusing the already-loaded row data.

**Files:**
- Create: `web/src/features/meals/MealDetailDialog.tsx`
- Modify: `web/src/features/meals/MealsPage.tsx`
- Modify: `web/src/features/meals/MealsPage.test.tsx`

**Interfaces:**
- Consumes: `Dialog`/`DialogContent`/`DialogTitle` (Task 5), `MealDetail` (Task 7), `Table.onRowClick` (Task 8).
- Produces: `MealDetailDialog({ meal: MealResponse | null, open: boolean, onOpenChange: (open: boolean) => void })`.

- [ ] **Step 1: Write the failing test**

Add to `web/src/features/meals/MealsPage.test.tsx` (the `MEALS` fixture already has full meal objects — add `servings: 2,` to its single meal, after `category`):

```tsx
it('opens a detail dialog when a meal row is clicked', async () => {
  server.use(http.get('http://localhost/api/meals/search', () => HttpResponse.json(MEALS)))
  renderMealsPage()
  fireEvent.click(await screen.findByText('Chicken Bowl'))
  expect(await screen.findByText(/makes 2 servings/i)).toBeInTheDocument()
  expect(screen.getByText('Cook chicken')).toBeInTheDocument()
})
```

- [ ] **Step 2: Run to verify failure**

Run: `cd web && npm test -- --run src/features/meals/MealsPage.test.tsx`
Expected: FAIL — clicking the row does nothing; the servings text never appears.

- [ ] **Step 3: Implement `MealDetailDialog.tsx`**

Create `web/src/features/meals/MealDetailDialog.tsx`:

```tsx
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog'
import type { MealResponse } from '@/api/types'
import { MealDetail } from '@/features/meals/MealDetail'

interface MealDetailDialogProps {
  meal: MealResponse | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function MealDetailDialog({ meal, open, onOpenChange }: MealDetailDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        {meal && (
          <>
            <DialogTitle className="sr-only">{meal.name}</DialogTitle>
            <MealDetail meal={meal} />
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
```

> `MealDetail` renders the visible `<h1>` title; the `sr-only` `DialogTitle` satisfies the dialog's accessible-name requirement without duplicating a visible heading.

- [ ] **Step 4: Wire the dialog into `MealsPage`**

In `web/src/features/meals/MealsPage.tsx`:

Add imports:

```tsx
import type { AddMealRequest, MealResponse, SearchParams } from '@/api/types'
import { MealDetailDialog } from '@/features/meals/MealDetailDialog'
```

(Replace the existing `import type { AddMealRequest, SearchParams } from '@/api/types'` line with the one above.)

Add selection state next to the other `useState` hooks:

```tsx
  const [selectedMeal, setSelectedMeal] = useState<MealResponse | null>(null)
```

Pass `onRowClick` to the `Table` (replace the existing `<Table ... />` props' closing by adding the handler):

```tsx
      <Table
        columns={[
          { key: 'name', header: 'Name' },
          { key: 'category', header: 'Category' },
          { key: 'macros', header: 'Calories', render: (v) => (v as { calories: number }).calories },
          { key: 'macros', header: 'Protein', render: (v) => `${(v as { protein: number }).protein}g` },
          { key: 'macros', header: 'Carbs', render: (v) => `${(v as { carbs: number }).carbs}g` },
          { key: 'macros', header: 'Fat', render: (v) => `${(v as { fat: number }).fat}g` },
        ]}
        rows={(meals ?? []) as unknown as Record<string, unknown>[]}
        onRowClick={(row) => setSelectedMeal(row as unknown as MealResponse)}
      />
      <MealDetailDialog
        meal={selectedMeal}
        open={selectedMeal !== null}
        onOpenChange={(open) => {
          if (!open) setSelectedMeal(null)
        }}
      />
```

- [ ] **Step 5: Run the meals tests + type check**

Run: `cd web && npm test -- --run src/features/meals && npx tsc --noEmit`
Expected: PASS; no type errors.

- [ ] **Step 6: Commit**

```bash
git add web/src/features/meals/MealDetailDialog.tsx web/src/features/meals/MealsPage.tsx web/src/features/meals/MealsPage.test.tsx
git commit -m "feat(web): open meal detail in a dialog from clickable rows (#6)"
```

---

### Task 10: `servings` input in the add-meal form

Let users set servings when adding a meal, and send it to the backend.

**Files:**
- Modify: `web/src/api/types.ts` (`AddMealRequest.servings`)
- Modify: `web/src/features/meals/MealsPage.tsx` (form state + input + payload)
- Modify: `web/src/features/meals/MealsPage.test.tsx`

**Interfaces:**
- Consumes: `api.meals.add` (unchanged signature; `AddMealRequest` gains `servings`).

- [ ] **Step 1: Add `servings` to the `AddMealRequest` type**

In `web/src/api/types.ts`, in `interface AddMealRequest`, add after `category`:

```ts
  servings: number
```

- [ ] **Step 2: Write the failing test**

Add to `web/src/features/meals/MealsPage.test.tsx`:

```tsx
it('sends servings in the add-meal payload', async () => {
  let body: AddMealRequest | null = null
  server.use(
    http.get('http://localhost/api/meals/search', () => HttpResponse.json([])),
    http.post('http://localhost/api/meals/add', async ({ request }) => {
      body = (await request.json()) as AddMealRequest
      return HttpResponse.json({
        success: true, meal_name: 'X', newly_added: [], category: 'Dinner', message: 'ok',
      })
    })
  )
  renderMealsPage()
  fireEvent.click(await screen.findByRole('button', { name: /add meal/i }))
  fireEvent.change(screen.getByLabelText(/meal name/i), { target: { value: 'X' } })
  fireEvent.change(screen.getByLabelText(/ingredients/i), { target: { value: 'Egg' } })
  fireEvent.change(screen.getByLabelText(/instructions/i), { target: { value: 'Cook' } })
  fireEvent.change(screen.getByLabelText(/servings/i), { target: { value: '4' } })
  fireEvent.click(screen.getByRole('button', { name: /save meal/i }))
  await waitFor(() => expect(body).not.toBeNull())
  expect(body!.servings).toBe(4)
})
```

Add `import type { AddMealRequest } from '@/api/types'` to the test file if not present.

- [ ] **Step 3: Run to verify failure**

Run: `cd web && npm test -- --run src/features/meals/MealsPage.test.tsx`
Expected: FAIL — no servings field; `getByLabelText(/servings/i)` not found.

- [ ] **Step 4: Add the form field + payload**

In `web/src/features/meals/MealsPage.tsx`:

Add `servings: '1'` to the initial `form` state object (after `category: 'Dinner',`):

```tsx
    instructions: '', category: 'Dinner', servings: '1', tags: '',
```

Add `servings` to the submitted request (in `handleAddSubmit`, in the `req` object after `category`):

```tsx
      servings: parseInt(form.servings) || 1,
```

Reset `servings` in the `onSuccess` `setForm({ ... })` call (add `servings: '1',`).

Add the input inside the Category/Tags grid. Replace the `<div className="grid grid-cols-2 gap-2">` block (Category + Tags) with a three-column grid that includes Servings:

```tsx
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Category</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm">
                {['Breakfast', 'Lunch', 'Dinner', 'Snack'].map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="meal-servings" className="block text-sm text-gray-600 mb-1">Servings</label>
              <input id="meal-servings" type="number" min="1" value={form.servings} onChange={(e) => setForm({ ...form, servings: e.target.value })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Tags (comma-separated)</label>
              <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} className="w-full border border-gray-300 rounded px-3 py-2 text-sm" />
            </div>
          </div>
```

> The existing "Instructions (semicolon-separated)" `<textarea>` has no `htmlFor`/`id`; the test selects it via `getByLabelText(/instructions/i)`, which matches its wrapping `<label>` text. If that lookup fails, add `htmlFor="meal-instructions"` to the label and `id="meal-instructions"` to the textarea.

- [ ] **Step 5: Run to verify pass + type check**

Run: `cd web && npm test -- --run src/features/meals/MealsPage.test.tsx && npx tsc --noEmit`
Expected: PASS; no type errors.

- [ ] **Step 6: Commit**

```bash
git add web/src/api/types.ts web/src/features/meals/MealsPage.tsx web/src/features/meals/MealsPage.test.tsx
git commit -m "feat(web): add servings input to the add-meal form (#6)"
```

---

### Task 11: Full verification + follow-up issue

Run both suites end to end and file the structured-ingredients follow-up.

**Files:** none (verification + issue creation).

- [ ] **Step 1: Backend full check**

Run: `uv run pytest tests/ -q && uv run black --check src/ && uv run mypy src/`
Expected: all PASS / clean.

- [ ] **Step 2: Frontend full check**

Run: `cd web && npm test -- --run && npx tsc --noEmit`
Expected: all tests PASS; no type errors.

- [ ] **Step 3: Manual smoke (optional but recommended)**

Start both servers (`uv run uvicorn src.api.main:app --reload` and, from `web/`, `npm run dev`), open the Meals tab, click a row → the dialog shows servings, macro tiles, the ratio bar, and numbered steps; resize narrow → the dialog becomes a bottom sheet; the `/meals/:name` page and Plan-page deep links still render.

- [ ] **Step 4: Create the follow-up issue**

Run:

```bash
gh issue create --repo evanmei87/meal-planner \
  --title "feat: structured ingredients — per-ingredient serving sizes + macros" \
  --label enhancement \
  --body "Follow-up to #6. Restructure \`ingredients\` from \`list[str]\` to objects \`{name, serving, calories, protein, carbs, fat}\`.

Scope:
- Data migration of \`src/data/meal-recipes.md\` ingredient cells to a structured encoding.
- Update the shared \`parse_recipe_row\` parser, \`MealResponse\`/\`AddMealRequest\` models, and \`add_saved_meal\` write path.
- Add per-ingredient serving sizes + macros to the add-meal form.
- Render a per-ingredient macro/serving table inside \`MealDetail\`.
- Reassess plan-generation ingredient scoring (\`generate_plan.py\`), which currently keys off ingredient-name strings.

Design context: \`docs/superpowers/specs/2026-06-30-click-into-meals-design.md\` (§2, §6)."
```

Expected: prints the new issue URL.

- [ ] **Step 5: Commit any remaining tracked changes**

```bash
git add -A && git commit -m "chore: verification pass for click-into-meals (#6)" --allow-empty
```

---

## Self-Review

**Spec coverage**
- Servings field (data + models + write path) → Tasks 1–4. ✓
- Richer instructions for the 5 meals → Task 4. ✓
- Parser consolidation (all three duplicates) → Tasks 1–2. ✓
- Clickable rows → detail Dialog (responsive, no `vaul`) → Tasks 5, 8, 9. ✓
- Shared `MealDetail` for Dialog + kept page → Task 7. ✓
- Macro tiles + ratio bar, no library → Task 6. ✓
- No `GET /meals/{name}` (reuse row data) → Task 9 design. ✓
- Add-meal servings input → Task 10. ✓
- Follow-up issue → Task 11. ✓

**Placeholder scan:** No TBD/TODO; every code step shows full code; the one CLI-generated file (Task 5) ships with a complete hand-authored fallback and a test that fixes its contract.

**Type consistency:** `parse_recipe_row` keys match between Tasks 1–3; `MealResponse.servings`/`AddMealRequest.servings` added before first use (Tasks 3, 7, 10); `MealDetail({ meal })`, `MacroBar({ protein, carbs, fat })`, `StatTile({ label, value })`, `Table.onRowClick(row)`, and `MealDetailDialog({ meal, open, onOpenChange })` signatures are consistent across the tasks that consume them.
