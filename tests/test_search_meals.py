import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tools.search_meals import search_meals

# --- Fixture helpers ---

SAMPLE_MEALS = [
    {
        'name': 'Chicken Bowl',
        'category': 'Dinner',
        'macros': {'calories': 600, 'protein': 45, 'carbs': 55, 'fat': 12},
        'ingredients': ['Chicken Breast', 'White Rice', 'Broccoli'],
        'instructions': ['Cook chicken', 'Cook rice'],
        'tags': ['high_protein', 'quick'],
    },
    {
        'name': 'Oatmeal',
        'category': 'Breakfast',
        'macros': {'calories': 400, 'protein': 15, 'carbs': 70, 'fat': 8},
        'ingredients': ['Oatmeal', 'Berries'],
        'instructions': ['Cook oatmeal'],
        'tags': ['vegetarian'],
    },
    {
        'name': 'Salmon Bowl',
        'category': 'Dinner',
        'macros': {'calories': 700, 'protein': 50, 'carbs': 45, 'fat': 25},
        'ingredients': ['Salmon', 'Quinoa', 'Spinach'],
        'instructions': ['Cook salmon', 'Cook quinoa'],
        'tags': ['high_protein'],
    },
]


def _patch_load(monkeypatch):
    import tools.search_meals as sm
    monkeypatch.setattr(sm, 'load_saved_meals', lambda: SAMPLE_MEALS)


# --- category filter ---

def test_search_meals_by_category(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'category': 'Breakfast'})
    assert len(results) == 1
    assert results[0]['name'] == 'Oatmeal'

def test_search_meals_category_no_match(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'category': 'Snack'})
    assert results == []


# --- search_term filter ---

def test_search_meals_by_name(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'search_term': 'salmon'})
    assert len(results) == 1
    assert results[0]['name'] == 'Salmon Bowl'

def test_search_meals_by_ingredient(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'search_term': 'quinoa'})
    assert len(results) == 1
    assert results[0]['name'] == 'Salmon Bowl'

def test_search_meals_by_tag(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'search_term': 'vegetarian'})
    assert len(results) == 1
    assert results[0]['name'] == 'Oatmeal'


# --- calorie range filters ---

def test_search_meals_min_cal(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'min_cal': 650})
    assert all(m['macros']['calories'] >= 650 for m in results)
    assert len(results) == 1
    assert results[0]['name'] == 'Salmon Bowl'

def test_search_meals_max_cal(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'max_cal': 500})
    assert all(m['macros']['calories'] <= 500 for m in results)
    assert len(results) == 1
    assert results[0]['name'] == 'Oatmeal'

def test_search_meals_cal_range(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'min_cal': 500, 'max_cal': 650})
    assert len(results) == 1
    assert results[0]['name'] == 'Chicken Bowl'


# --- protein filters ---

def test_search_meals_min_prot(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'min_prot': 45})
    names = [m['name'] for m in results]
    assert 'Chicken Bowl' in names
    assert 'Salmon Bowl' in names
    assert 'Oatmeal' not in names

def test_search_meals_max_prot(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'max_prot': 20})
    assert len(results) == 1
    assert results[0]['name'] == 'Oatmeal'


# --- ingredient filter ---

def test_search_meals_by_ingredient_filter(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'ingredient': 'Chicken Breast'})
    assert len(results) == 1
    assert results[0]['name'] == 'Chicken Bowl'

def test_search_meals_ingredient_partial_match(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'ingredient': 'chicken'})
    assert len(results) == 1


# --- tag filter ---

def test_search_meals_by_tag(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'tag': 'high_protein'})
    assert len(results) == 2
    names = [m['name'] for m in results]
    assert 'Chicken Bowl' in names
    assert 'Salmon Bowl' in names

def test_search_meals_by_tag_no_match(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'tag': 'keto'})
    assert results == []


# --- combined filters ---

def test_search_meals_combined_filters(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({'category': 'Dinner', 'min_prot': 48})
    assert len(results) == 1
    assert results[0]['name'] == 'Salmon Bowl'

def test_search_meals_empty_criteria(monkeypatch):
    _patch_load(monkeypatch)
    results = search_meals({})
    assert len(results) == 3
