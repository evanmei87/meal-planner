# LLM Preference Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace brittle keyword matching for dietary preferences with Gemini-powered normalization that handles misspellings, synonyms, and category terms (e.g. "no chickn" and "no poultry" both correctly exclude chicken meals).

**Architecture:** When the user saves preferences via `PUT /state/`, the endpoint calls a new `normalize_preferences()` function that sends the raw string to Gemini and gets back a grounded list of exact ingredient/meal name terms to exclude. Both the raw string (`preferences`) and the resolved list (`normalized_exclusions`) are persisted in state.json. The plan generator reads `normalized_exclusions` for filtering (falling back to keyword parsing if absent for backward compatibility). This means Gemini is called once on Save — never on plan generation.

**Tech Stack:** Python, FastAPI, Pydantic v2, `google-genai` (`GeminiAgent` in `src/tools/llm_agent.py`), pytest, React + TypeScript.

## Global Constraints

- Model: `gemini-2.5-flash-lite` (already configured as `DEFAULT_MODEL` in `llm_agent.py`)
- Normalizer must fall back to simple keyword parsing if Gemini call fails for any reason
- Only touch the listed files — do not restructure unrelated code
- Follow existing pytest style: `tmp_path` for temp files, plain `assert`, `monkeypatch` for external calls
- `normalized_exclusions` terms must be stored as **lowercase** strings
- Gemini output is grounded in `KNOWN_MEAL_TERMS` — the prompt only asks for terms from that list

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/tools/preference_normalizer.py` | Call Gemini, return exclusion list, fallback |
| Create | `tests/test_preference_normalizer.py` | Unit tests for normalizer |
| Modify | `src/api/models.py` | Add `normalized_exclusions` to `StateResponse` + `UpdateStateRequest` |
| Modify | `src/tools/update_state.py` | Persist `normalized_exclusions` field |
| Modify | `src/api/endpoints/state.py` | Call normalizer on Save, include in update payload |
| Modify | `src/tools/generate_plan.py` | Prefer `normalized_exclusions` over keyword parse; update both filtering sites |
| Modify | `web/src/api/types.ts` | Add `normalized_exclusions?: string[]` to `AppState` |
| Modify | `CLAUDE.md` | Add Gemini API free tier info under new "External APIs" section |

---

### Task 1: Preference normalizer + generate_plan wiring

**Files:**
- Create: `src/tools/preference_normalizer.py`
- Create: `tests/test_preference_normalizer.py`
- Modify: `src/tools/generate_plan.py`
- Test: `tests/test_generate_plan.py`

**Interfaces:**
- Produces: `normalize_preferences(preferences: str) -> list[str]` — import this in the state endpoint (Task 2)
- Produces: `_fallback_exclusions(preferences: str) -> list[str]` — used internally for fallback
- `KNOWN_MEAL_TERMS: list[str]` — list of lowercase ingredient and meal name strings that grounds Gemini output

- [ ] **Step 1: Create `src/tools/preference_normalizer.py`**

```python
from pydantic import BaseModel
from src.tools.llm_agent import GeminiAgent

KNOWN_MEAL_TERMS = [
    # meal names
    "oatmeal with berries", "oatmeal with greek yogurt",
    "oatmeal with scrambled eggs", "oatmeal and protein shake",
    "chicken thigh stir-fry with rice", "salmon rice bowl",
    "grilled chicken rice plate", "salmon quinoa bowl",
    "chicken breast with quinoa", "salmon with quinoa and spinach",
    "protein shake (2 scoops)",
    "greek yogurt with nuts", "cottage cheese", "hard-boiled eggs",
    # ingredients
    "oatmeal", "mixed berries", "milk", "greek yogurt", "honey",
    "eggs", "butter", "protein powder", "almond milk", "white rice",
    "quinoa", "soy sauce", "olive oil", "mixed nuts", "cottage cheese",
    "chicken thighs", "chicken breast", "salmon",
    "mushrooms", "spinach", "bell peppers", "green beans", "broccoli", "banana",
]

_KNOWN_TERMS_TEXT = ", ".join(KNOWN_MEAL_TERMS)


class _PreferenceExclusions(BaseModel):
    excluded_terms: list[str]


def normalize_preferences(preferences: str) -> list[str]:
    """Return lowercase exclusion terms derived from a natural-language preferences string.

    Calls Gemini to handle misspellings, synonyms, and category terms.
    Falls back to simple 'no X' keyword parsing on any error.
    """
    if not preferences or not preferences.strip():
        return []

    prompt = (
        f'The user has these dietary preferences: "{preferences}"\n\n'
        "Identify which items from the known list below should be EXCLUDED based on "
        "the user's preferences. Consider misspellings, synonyms, and category terms "
        '(e.g. "no dairy" → exclude milk, butter, greek yogurt, almond milk; '
        '"no poultry" → exclude chicken thighs, chicken breast; '
        '"vegetarian" → exclude chicken thighs, chicken breast, salmon).\n\n'
        f"Known meal names and ingredients: {_KNOWN_TERMS_TEXT}\n\n"
        'Return a JSON object with "excluded_terms": a list of lowercase strings '
        "taken from the known list above. Return an empty list if nothing applies."
    )

    try:
        result = GeminiAgent().process(prompt, response_schema=_PreferenceExclusions)
        return [t.lower().strip() for t in result.excluded_terms if t.strip()]
    except Exception:
        return _fallback_exclusions(preferences)


def _fallback_exclusions(preferences: str) -> list[str]:
    """Simple 'no X' parser used when the Gemini call fails."""
    excluded = []
    for phrase in preferences.lower().split(","):
        phrase = phrase.strip()
        if phrase.startswith("no "):
            excluded.append(phrase[3:].strip())
    return excluded
```

- [ ] **Step 2: Write failing tests in `tests/test_preference_normalizer.py`**

```python
import pytest
import sys
from pathlib import Path
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.preference_normalizer import normalize_preferences, _fallback_exclusions


class _FakeAgent:
    def __init__(self, terms):
        self._terms = terms

    def process(self, prompt, response_schema=None):
        return response_schema(excluded_terms=self._terms)


class _FailingAgent:
    def process(self, prompt, response_schema=None):
        raise RuntimeError("API unavailable")


def _patch_agent(monkeypatch, agent):
    monkeypatch.setattr("tools.preference_normalizer.GeminiAgent", lambda: agent)


def test_normalize_empty_string_returns_empty():
    assert normalize_preferences("") == []


def test_normalize_whitespace_only_returns_empty():
    assert normalize_preferences("   ") == []


def test_normalize_calls_gemini_and_returns_terms(monkeypatch):
    _patch_agent(monkeypatch, _FakeAgent(["chicken thighs", "chicken breast"]))
    result = normalize_preferences("no chicken")
    assert "chicken thighs" in result
    assert "chicken breast" in result


def test_normalize_lowercases_gemini_output(monkeypatch):
    _patch_agent(monkeypatch, _FakeAgent(["Salmon", "OATMEAL"]))
    result = normalize_preferences("no fish, no grains")
    assert all(t == t.lower() for t in result)


def test_normalize_falls_back_on_gemini_error(monkeypatch):
    _patch_agent(monkeypatch, _FailingAgent())
    result = normalize_preferences("no salmon")
    assert "salmon" in result


def test_fallback_exclusions_parses_no_phrases():
    assert _fallback_exclusions("no salmon, no chicken") == ["salmon", "chicken"]


def test_fallback_exclusions_ignores_non_no_phrases():
    assert _fallback_exclusions("high protein, no red meat") == ["red meat"]


def test_fallback_exclusions_empty():
    assert _fallback_exclusions("") == []
```

- [ ] **Step 3: Run tests — expect all to fail**

```bash
uv run pytest tests/test_preference_normalizer.py -q
```

Expected: import errors or failures.

- [ ] **Step 4: Run tests — expect all to pass after Step 1**

```bash
uv run pytest tests/test_preference_normalizer.py -q
```

Expected: 8 passed.

- [ ] **Step 5: Update `generate_plan.py` — `_build_candidate_meals` uses `normalized_exclusions` when present**

In `_build_candidate_meals`, replace the two lines that compute `preferences`/`excluded` with:

```python
    normalized = state.get('normalized_exclusions')
    if normalized is not None:
        excluded = [t.lower() for t in normalized]
    else:
        preferences = state.get('preferences', '') or ''
        excluded = _excluded_terms(preferences)
    combined = [m for m in combined if _meal_allowed(m, excluded)]
```

(The rest of the function — `inventory_names`, scoring, sort — is unchanged.)

- [ ] **Step 6: Update `generate_day_plan` fallback path for the same preference lookup**

In `generate_day_plan`, the two blocks that compute `preferences`/`excluded` for the fallback path should each be replaced with:

```python
        normalized = state.get('normalized_exclusions')
        if normalized is not None:
            excluded = [t.lower() for t in normalized]
        else:
            preferences = state.get('preferences', '') or ''
            excluded = _excluded_terms(preferences)
```

There are two such blocks (one inside `if candidates:` and one in the `else:` branch). Update both.

- [ ] **Step 7: Add a test for `normalized_exclusions` in `tests/test_generate_plan.py`**

Add this test:

```python
def test_generate_plan_uses_normalized_exclusions_over_keyword_parse(tmp_path, monkeypatch):
    """normalized_exclusions takes priority over keyword-parsing state.preferences."""
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
        'preferences': 'ignore this',
        # normalized list explicitly excludes salmon
        'normalized_exclusions': ['salmon', 'salmon rice bowl', 'salmon quinoa bowl',
                                   'salmon with quinoa and spinach'],
    }
    state_file = tmp_path / 'state.json'
    state_file.write_text(json.dumps(state))

    monkeypatch.setattr('tools.generate_plan.get_inventory', lambda: [])
    monkeypatch.setattr('tools.generate_plan.load_saved_meals', lambda: [])

    result = generate_meal_plan_from_request(str(state_file), {'days': ['Monday']})

    all_meal_names = [m['name'] for day in result['plan'] for m in day['meals']]
    assert not any('salmon' in name.lower() for name in all_meal_names)
```

- [ ] **Step 8: Run all generate_plan and normalizer tests**

```bash
uv run pytest tests/test_preference_normalizer.py tests/test_generate_plan.py -q
```

Expected: all pass (18+ tests).

- [ ] **Step 9: Commit**

```bash
git add src/tools/preference_normalizer.py tests/test_preference_normalizer.py src/tools/generate_plan.py tests/test_generate_plan.py
git commit -m "feat: add Gemini preference normalizer; wire normalized_exclusions into meal filtering (#9)"
```

---

### Task 2: Persist normalized_exclusions through state + call normalizer on Save

**Files:**
- Modify: `src/api/models.py`
- Modify: `src/tools/update_state.py`
- Modify: `src/api/endpoints/state.py`
- Test: `tests/test_update_state.py`, `tests/test_api/`

**Interfaces:**
- Consumes: `normalize_preferences(preferences: str) -> list[str]` from `src/tools/preference_normalizer.py`
- `UpdateStateRequest.normalized_exclusions: Optional[List[str]] = None`
- `StateResponse.normalized_exclusions: Optional[List[str]] = None`

- [ ] **Step 1: Add `normalized_exclusions` field to models in `src/api/models.py`**

In `StateResponse`, add after the `preferences` field:

```python
    normalized_exclusions: Optional[List[str]] = None
```

In `UpdateStateRequest`, add after the `preferences` field:

```python
    normalized_exclusions: Optional[List[str]] = None
```

- [ ] **Step 2: Handle `normalized_exclusions` in `src/tools/update_state.py`**

Add after the existing `if 'preferences' in updated_plan:` block:

```python
        if 'normalized_exclusions' in updated_plan:
            existing_state['normalized_exclusions'] = updated_plan['normalized_exclusions']
```

- [ ] **Step 3: Update `src/api/endpoints/state.py` — call normalizer on Save**

At the top of the file add:

```python
from src.tools.preference_normalizer import normalize_preferences
```

In the `update_state_endpoint` function, replace the existing preferences block:

```python
        if request.preferences is not None:
            update_data['preferences'] = request.preferences
```

with:

```python
        if request.preferences is not None:
            update_data['preferences'] = request.preferences
            update_data['normalized_exclusions'] = normalize_preferences(request.preferences)
```

In the `StateResponse` return at the bottom of `update_state_endpoint`, add `normalized_exclusions` to the merged state response:

```python
        return StateResponse(
            current_day=merged_state.get('current_day', 'Monday'),
            plan_id=merged_state.get('plan_id', 'unknown'),
            plan=merged_state.get('plan', []),
            grocery_list=merged_state.get('grocery_list', []),
            missing_macros=merged_state.get('missing_macros', []),
            grocery_inventory=merged_state.get('grocery_inventory', []),
            unmatched_groceries=merged_state.get('unmatched_groceries', []),
            inventory_usage=merged_state.get('inventory_usage', {"used": [], "unused": [], "supplemental": []}),
            preferences=merged_state.get('preferences'),
            normalized_exclusions=merged_state.get('normalized_exclusions'),
        )
```

Also update the `get_state` endpoint's `StateResponse` return to include `normalized_exclusions`:

```python
        return StateResponse(
            current_day=state.get('current_day', 'Monday'),
            plan_id=state.get('plan_id', 'unknown'),
            plan=state.get('plan', []),
            grocery_list=state.get('grocery_list', []),
            missing_macros=state.get('missing_macros', []),
            grocery_inventory=state.get('grocery_inventory', []),
            unmatched_groceries=state.get('unmatched_groceries', []),
            inventory_usage=state.get('inventory_usage', {"used": [], "unused": [], "supplemental": []}),
            preferences=state.get('preferences'),
            normalized_exclusions=state.get('normalized_exclusions'),
        )
```

Also update the no-file fallback in `get_state`:

```python
            return StateResponse(
                current_day='Monday',
                plan_id='',
                plan=[],
                grocery_list=[],
                missing_macros=[],
                grocery_inventory=[],
                unmatched_groceries=[],
                inventory_usage={"used": [], "unused": [], "supplemental": []},
                preferences=None,
                normalized_exclusions=None,
            )
```

- [ ] **Step 4: Add test to `tests/test_update_state.py`**

```python
def test_update_state_persists_normalized_exclusions(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({'current_day': 'Monday', 'plan': [], 'grocery_list': [], 'missing_macros': []}))

    success = update_state(str(state_file), {'normalized_exclusions': ['salmon', 'oatmeal']})
    assert success is True

    saved = json.loads(state_file.read_text())
    assert saved['normalized_exclusions'] == ['salmon', 'oatmeal']
```

- [ ] **Step 5: Run all backend tests**

```bash
uv run pytest tests/ -q --ignore=tests/test_llm_agent.py --ignore=tests/test_food_processor.py
```

Expected: all pass (existing + new tests). The LLM tests are skipped because they require live API keys.

- [ ] **Step 6: Commit**

```bash
git add src/api/models.py src/tools/update_state.py src/api/endpoints/state.py tests/test_update_state.py
git commit -m "feat: persist normalized_exclusions in state; call Gemini normalizer on preference Save (#9)"
```

---

### Task 3: Frontend types + Gemini API docs

**Files:**
- Modify: `web/src/api/types.ts`
- Modify: `CLAUDE.md`

**Interfaces:**
- `AppState.normalized_exclusions?: string[]` — available to frontend if needed for display

- [ ] **Step 1: Add `normalized_exclusions` to `AppState` in `web/src/api/types.ts`**

In the `AppState` interface, add after `preferences?`:

```typescript
  normalized_exclusions?: string[]
```

- [ ] **Step 2: Run frontend type check**

```bash
cd web && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Add Gemini API section to `CLAUDE.md`**

Add this section after the existing `## Architecture` section (before `## Planning`):

````markdown
## External APIs

### Gemini API (Google AI)

Used for:
- **Grocery parsing** (`src/tools/food_processor.py` + `src/tools/llm_agent.py`)
- **Preference normalization** (`src/tools/preference_normalizer.py`) — called once when user saves preferences

**Setup:** Set `GEMINI_API_KEY` in a `.env` file at the project root. The key is read by `_read_env_file_api_key()` in `src/tools/llm_agent.py`.

```
GEMINI_API_KEY=your-key-here
```

**Model:** `gemini-2.5-flash-lite` (configured as `DEFAULT_MODEL` in `llm_agent.py`).

**Free tier:** Available at [ai.google.dev](https://ai.google.dev). Google does not publish static rate-limit numbers — check your current limits in [AI Studio → Rate Limits](https://aistudio.google.com/rate-limit). As of mid-2026 the free tier supports on the order of tens of requests per minute and hundreds to low thousands per day for Flash-class models. See [pricing page](https://ai.google.dev/gemini-api/docs/pricing) for input/output token costs on paid tier.

**Calls per user action:**
| Action | Gemini calls |
|--------|-------------|
| Save preferences (PUT /state/) | 1 — preference normalization |
| Parse groceries (POST /groceries/) | 1 per parse request |
| Regenerate plan (POST /plan/generate) | 0 |

Preference normalization only fires on explicit Save, so a typical session makes 1–3 Gemini calls total. The free tier is more than sufficient for personal or development use. If the API key is missing or the call fails, preference normalization falls back to simple keyword matching — the app stays functional.
````

- [ ] **Step 4: Run frontend tests to confirm nothing broke**

```bash
cd web && npm test -- --run
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add web/src/api/types.ts CLAUDE.md
git commit -m "docs: add Gemini API free tier info to CLAUDE.md; add normalized_exclusions to AppState (#9)"
```
