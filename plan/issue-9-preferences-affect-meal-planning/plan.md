# Plan: Bug — Preferences Don't Affect Meal Planning

**GitHub Issue**: https://github.com/evanmei87/meal-planner/issues/9

## Summary

User preferences saved in `state.preferences` (e.g. "no salmon, no chicken") are never
consulted when generating the meal plan. The generator picks meals from hardcoded and saved
meal options with no preference filtering.

**Note**: The GitHub issue plan mentioned a "Gemini prompt" but the meal planner is entirely
algorithmic — there is no LLM call in `generate_plan.py`. The fix is keyword-based filtering.

**Note**: The frontend display of preferences (bug 2 in the issue) was already fixed in PR #8
(feat/5-preferences-enhance). No frontend work is needed.

## Global Constraints

- Only touch `src/tools/generate_plan.py` and `tests/test_generate_plan.py`
- Do not add LLM calls or external dependencies
- Keep changes minimal and algorithmic
- Follow existing test style (pytest, tmp_path, plain assert)
- `state.preferences` is a comma-separated string, e.g. `"no salmon, no chicken"`
- Filtering applies to `_build_candidate_meals`; meals must still fall back to
  `_fallback_day_meals` if all candidates are filtered out (existing behavior preserved)

## Task 1: Filter candidate meals by state.preferences

**File**: `src/tools/generate_plan.py`

### What to implement

Add two pure helper functions above `_build_candidate_meals`:

```python
def _excluded_terms(preferences: str) -> list[str]:
    """Extract excluded ingredient/meal terms from a preferences string.

    Parses comma-separated phrases of the form "no X" and returns [X, ...].
    Other phrases (e.g. "high protein") are ignored.
    """
    excluded = []
    for phrase in preferences.lower().split(','):
        phrase = phrase.strip()
        if phrase.startswith('no '):
            excluded.append(phrase[3:].strip())
    return excluded


def _meal_allowed(meal: dict, excluded: list[str]) -> bool:
    """Return True if no excluded term appears in the meal name or ingredients."""
    if not excluded:
        return True
    meal_text = (meal.get('name', '') + ' ' + ' '.join(meal.get('ingredients', []))).lower()
    return not any(term in meal_text for term in excluded)
```

Then modify `_build_candidate_meals` to accept and apply preferences:

```python
def _build_candidate_meals(state: dict, inventory: list[dict]) -> list[dict]:
    # ... existing code to build combined list ...
    
    preferences = state.get('preferences', '') or ''
    excluded = _excluded_terms(preferences)
    combined = [m for m in combined if _meal_allowed(m, excluded)]

    # ... existing scoring code unchanged ...
```

### Tests to write in `tests/test_generate_plan.py`

Import `_excluded_terms`, `_meal_allowed`, and `generate_meal_plan_from_request`.

```python
def test_excluded_terms_parses_no_phrases():
    assert _excluded_terms('no salmon, no chicken') == ['salmon', 'chicken']

def test_excluded_terms_ignores_non_no_phrases():
    assert _excluded_terms('high protein, no red meat') == ['red meat']

def test_excluded_terms_empty():
    assert _excluded_terms('') == []

def test_meal_allowed_passes_when_no_exclusions():
    meal = {'name': 'Salmon Rice Bowl', 'ingredients': ['Salmon', 'Rice']}
    assert _meal_allowed(meal, []) is True

def test_meal_allowed_filters_by_name():
    meal = {'name': 'Salmon Rice Bowl', 'ingredients': ['Salmon', 'Rice']}
    assert _meal_allowed(meal, ['salmon']) is False

def test_meal_allowed_filters_by_ingredient():
    meal = {'name': 'Rice Bowl', 'ingredients': ['Salmon', 'Rice']}
    assert _meal_allowed(meal, ['salmon']) is False

def test_meal_allowed_case_insensitive():
    meal = {'name': 'Salmon Rice Bowl', 'ingredients': ['Salmon', 'Rice']}
    assert _meal_allowed(meal, ['Salmon']) is False

def test_generate_meal_plan_from_request_respects_state_preferences(tmp_path, monkeypatch):
    """Meals matching state.preferences exclusions must not appear in the plan."""
    import json
    from tools.generate_plan import generate_meal_plan_from_request

    state = {
        'current_day': 'Monday',
        'plan_id': 'test-id',
        'plan': [],
        'grocery_list': [],
        'missing_macros': [],
        'grocery_inventory': [],
        'unmatched_groceries': [],
        'inventory_usage': {'used': [], 'unused': [], 'supplemental': []},
        'preferences': 'no salmon',
    }
    state_file = tmp_path / 'state.json'
    state_file.write_text(json.dumps(state))

    monkeypatch.setattr('tools.generate_plan.get_inventory', lambda: [])
    monkeypatch.setattr('tools.generate_plan.load_saved_meals', lambda: [])

    result = generate_meal_plan_from_request(str(state_file), {'days': ['Monday']})

    all_meal_names = [m['name'] for day in result['plan'] for m in day['meals']]
    assert not any('salmon' in name.lower() for name in all_meal_names)
```

### Verification

```bash
uv run pytest tests/test_generate_plan.py -q
```

All tests must pass.

### Commit

```
fix: filter candidate meals by state.preferences exclusions (#9)
```
