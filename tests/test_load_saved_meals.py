import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.load_saved_meals import load_saved_meals, format_meals_markdown, format_meals_cli

# --- Fixture helpers ---

RECIPES_CONTENT_EMPTY = ""

RECIPES_CONTENT = """\
<!-- meal-recipes.md -->
<!-- name | version | category | servings | macros(cal,prot,carb,fat) | ingredients | instructions | tags -->

| name | version | category | servings | macros | ingredients | instructions | tags |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Chicken Bowl | 2024-01-01T00:00:00 | Dinner | 1 | 600,45,55,12 | Chicken Breast, White Rice, Broccoli | Cook chicken;Cook rice;Steam broccoli | high_protein,quick |
| Oatmeal | 2024-01-02T00:00:00 | Breakfast | 1 | 400,15,70,8 | Oatmeal, Berries | Cook oatmeal;Add berries | vegetarian |
| Salmon Bowl | 2024-01-03T00:00:00 | Dinner | 2 | 700,50,45,25 | Salmon, Quinoa, Spinach | Cook salmon;Cook quinoa | high_protein |
"""


def _patched_load_meals(monkeypatch, content):
    """Monkeypatch load_static_data to return content without reading disk."""
    import tools.load_saved_meals as lsm
    monkeypatch.setattr(lsm, 'load_static_data', lambda: {'recipes': content})


# --- load_saved_meals ---

def test_load_saved_meals_empty(monkeypatch):
    _patched_load_meals(monkeypatch, RECIPES_CONTENT_EMPTY)
    assert load_saved_meals() == []

def test_load_saved_meals_returns_all(monkeypatch):
    _patched_load_meals(monkeypatch, RECIPES_CONTENT)
    meals = load_saved_meals()
    assert len(meals) == 3

def test_load_saved_meals_parses_fields(monkeypatch):
    _patched_load_meals(monkeypatch, RECIPES_CONTENT)
    meals = load_saved_meals()
    chicken = meals[0]
    assert chicken['name'] == 'Chicken Bowl'
    assert chicken['category'] == 'Dinner'
    assert chicken['macros']['calories'] == 600
    assert chicken['macros']['protein'] == 45
    assert 'Chicken Breast' in chicken['ingredients']
    assert 'high_protein' in chicken['tags']
    assert chicken['servings'] == 1

def test_load_saved_meals_filter_by_category(monkeypatch):
    _patched_load_meals(monkeypatch, RECIPES_CONTENT)
    meals = load_saved_meals(filter_category='Breakfast')
    assert len(meals) == 1
    assert meals[0]['name'] == 'Oatmeal'

def test_load_saved_meals_filter_case_insensitive(monkeypatch):
    _patched_load_meals(monkeypatch, RECIPES_CONTENT)
    meals = load_saved_meals(filter_category='dinner')
    assert len(meals) == 2

def test_load_saved_meals_search_by_name(monkeypatch):
    _patched_load_meals(monkeypatch, RECIPES_CONTENT)
    meals = load_saved_meals(search_term='salmon')
    assert len(meals) == 1
    assert meals[0]['name'] == 'Salmon Bowl'

def test_load_saved_meals_search_by_ingredient(monkeypatch):
    _patched_load_meals(monkeypatch, RECIPES_CONTENT)
    meals = load_saved_meals(search_term='quinoa')
    assert len(meals) == 1
    assert meals[0]['name'] == 'Salmon Bowl'

def test_load_saved_meals_search_by_tag(monkeypatch):
    _patched_load_meals(monkeypatch, RECIPES_CONTENT)
    meals = load_saved_meals(search_term='vegetarian')
    assert len(meals) == 1
    assert meals[0]['name'] == 'Oatmeal'

def test_load_saved_meals_no_results(monkeypatch):
    _patched_load_meals(monkeypatch, RECIPES_CONTENT)
    meals = load_saved_meals(search_term='nonexistent_food_xyz')
    assert meals == []


# --- format_meals_markdown ---

def test_format_meals_markdown_empty():
    result = format_meals_markdown([])
    assert result == "No meals found."

def test_format_meals_markdown_contains_name(monkeypatch):
    _patched_load_meals(monkeypatch, RECIPES_CONTENT)
    meals = load_saved_meals()
    result = format_meals_markdown(meals)
    assert 'Chicken Bowl' in result
    assert '## Saved Meals' in result


# --- format_meals_cli ---

def test_format_meals_cli_empty():
    result = format_meals_cli([])
    assert result == "No meals found."

def test_format_meals_cli_contains_name(monkeypatch):
    _patched_load_meals(monkeypatch, RECIPES_CONTENT)
    meals = load_saved_meals()
    result = format_meals_cli(meals)
    assert 'Chicken Bowl' in result
    assert 'Dinner' in result
