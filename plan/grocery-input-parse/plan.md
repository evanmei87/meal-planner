# Grocery-Driven Meal Planning: Expanded Implementation Plan

## Summary
Build a CLI-first feature where the user describes what they bought in natural language, Gemini parses it into structured grocery items, the backend matches each item to `src/data/food.csv` or manual specialty macros, saves the result as grocery inventory, and meal generation uses that inventory first. If inventory is incomplete, the generated `grocery_list` becomes the supplemental list of what still needs to be bought.

Official SDK reference: https://ai.google.dev/gemini-api/docs/migrate

## Interfaces And Data Contracts
- Add dependency declarations for `google-genai` and ensure `pydantic` is declared in both `requirements.txt` and `pyproject.toml`.
- Add a reusable confidence module at `src/tools/confidence.py` for all LLM-assisted workflows, not just grocery parsing.
- Confidence scores are always floats on a normalized `0.0` to `1.0` scale.
- Shared confidence defaults:
  - `HIGH_CONFIDENCE_THRESHOLD = 0.7`.
  - `REVIEW_CONFIDENCE_THRESHOLD = 0.4`.
  - `score >= 0.7`: high confidence and eligible for auto-save.
  - `0.4 <= score < 0.7`: review confidence and requires user confirmation.
  - `score < 0.4`: low confidence and should go to manual resolution or macro entry.
- The reusable confidence module should expose:
  - `ConfidenceResult(score, level, should_auto_save, reason=None)`.
  - `classify_confidence(score: float, high_threshold: float = 0.7, review_threshold: float = 0.4) -> ConfidenceResult`.
  - `format_confidence(score: float) -> str`, returning display text such as `0.83`.
- New parser output schema:
  - `IngredientItem(raw_phrase, standardized_item, quantity, unit, corgis_style_query)`.
  - `IngredientResponseSchema(ingredients: list[IngredientItem])`.
- Matched ingredient records must include:
  - `raw_phrase`, `standardized_item`, `quantity`, `unit`, `corgis_style_query`.
  - `corgis_description`, `corgis_category`, `nutrient_data_bank_number`.
  - `confidence_score`, `confidence_level`, `should_auto_save`.
  - `source`, using `corgis` or `specialty`.
- New persisted state fields:
  - `grocery_inventory`: matched usable groceries.
  - `unmatched_groceries`: items awaiting macro entry or match resolution.
  - `inventory_usage`: last generation's `{used, unused, supplemental}` summary.
- Keep existing `grocery_list` backward compatible, but redefine it during inventory-driven generation as "still need to buy."
- Store parser/matcher cache at `src/state/phrase_cache.json`; do not cache entire user paragraphs, cache normalized ingredient phrases.
- Match confidence thresholds must use the reusable confidence module:
  - `>= 0.7`: auto-save.
  - `0.4-0.699`: prompt user to accept match, enter macros, or skip.
  - `< 0.4` or no match: prompt for manual macros and append to `specialty-ingredients.md`.
- Every parsed ingredient result returned to a CLI caller must include `confidence_score` and `confidence_level`, even when the item is auto-saved.
- Unit handling for v1:
  - Normalize plural/singular for compatible units only: `lb/lbs`, `cup/cups`, `count/whole`, `tbsp`, `oz`, `scoop/scoops`.
  - Do not convert volume to weight.

## Implementation Tasks
1. **Add Dependencies And State Defaults**
   Context: `requirements.txt`, `pyproject.toml`, `src/tools/generate_plan.py`, `src/tools/update_state.py`.
   Add `google-genai`; add default empty values for `grocery_inventory`, `unmatched_groceries`, and `inventory_usage` wherever default state is created or merged.
   Verification: `uv run pytest tests/test_generate_plan.py::test_load_state_default tests/test_update_state.py -q`.

2. **Create Reusable Gemini Agent**
   Context: new `src/tools/llm_agent.py`.
   Implement `GeminiAgent` using `from google import genai` and `google.genai.types.GenerateContentConfig`; constructor defaults to `gemini-2.5-flash`; `process()` returns `response.parsed` when available and falls back to `response_schema.model_validate_json(response.text)`.
   Verification: `uv run pytest tests/test_llm_agent.py -q` with mocked `genai.Client`.

3. **Create Reusable Confidence Module**
   Context: new `src/tools/confidence.py`.
   Implement the shared 0-1 confidence API for LLM-backed work. Grocery parsing is the first consumer, but the module must be domain-neutral so future recipe parsing, workout parsing, and meal-plan generation can reuse it without importing grocery-specific code.
   Expected exports: `ConfidenceResult`, `classify_confidence()`, `format_confidence()`, `HIGH_CONFIDENCE_THRESHOLD = 0.7`, and `REVIEW_CONFIDENCE_THRESHOLD = 0.4`.
   Verification: `uv run pytest tests/test_confidence.py -q`.

4. **Create Ingredient Parser Schemas And Prompt**
   Context: new `src/tools/food_processor.py`.
   Define Pydantic schemas and a single system prompt matching the user's culinary parsing requirements: quantities as floats, units separated, noun-first CORGIS-style queries.
   Verification: `uv run pytest tests/test_food_processor.py::test_parser_schema_accepts_expected_payload -q`.

5. **Implement CORGIS Food CSV Matcher**
   Context: `src/data/food.csv`, new `src/tools/food_processor.py`, new `src/tools/confidence.py`.
   Load `Category`, `Description`, and `Nutrient Data Bank Number`; fuzzy-match against `Description`; compute a normalized `0.0-1.0` confidence score; classify the score through `src/tools/confidence.py`; return match metadata with `confidence_score`, `confidence_level`, `should_auto_save`, `category`, `corgis_description`, and nutrient id. Cache by lowercase `raw_phrase`.
   Verification: `uv run pytest tests/test_food_processor.py::test_corgis_matcher_finds_known_foods tests/test_food_processor.py::test_phrase_cache_bypasses_llm_match tests/test_food_processor.py::test_matcher_returns_confidence_contract -q`.

6. **Refactor Manual Macro Fallback**
   Context: `src/tools/add_saved_meal.py`, `src/data/specialty-ingredients.md`.
   Extract reusable helpers for validating macro entry and appending a specialty ingredient. Grocery parsing should call these helpers when no CORGIS match is acceptable.
   Verification: `uv run pytest tests/test_add_saved_meal.py tests/test_grocery_inventory.py::test_unmatched_item_can_be_saved_as_specialty_macro -q`.

7. **Build Inventory Persistence Layer**
   Context: new `src/tools/grocery_inventory.py`, `src/tools/generate_plan.py`.
   Add functions to merge parsed items into `grocery_inventory`, combine duplicate compatible item/unit pairs, preserve match metadata including `confidence_score` and `confidence_level`, and format inventory for CLI display. Mark perishables by category/name: protein, dairy, vegetable, fruit.
   Verification: `uv run pytest tests/test_grocery_inventory.py -q`.

8. **Add CLI Grocery Commands In `main.py`**
   Context: `main.py`.
   Add `groceries add --text`, `groceries list`, and `groceries clear`. `add --text` parses, auto-saves high-confidence matches with `confidence_score >= 0.7`, prompts for ambiguous/unmatched items, prints a compact save summary, and supports `--generate` to immediately run planning.
   The `groceries add --text` output must list every parsed entry with at least: raw phrase, standardized item, quantity, unit, CORGIS match or manual status, `confidence_score`, `confidence_level`, and saved/review/manual status.
   Example output shape: `chicken thighs | qty=2 lb | match=Chicken thigh, ... | confidence=0.86 high | saved=auto`.
   Verification: `uv run pytest tests/test_cli_groceries.py -q`.

9. **Add Interactive CLI Grocery Commands In `src/server.py`**
   Context: `src/server.py`.
   Add `add_groceries [natural text]`, `show_inventory`, and `clear_inventory` to the interactive prompt. If `add_groceries` is entered without trailing text, prompt for a full sentence. After saving, ask whether to generate a plan now. Match the same confidence-score display used by `main.py groceries add --text`.
   Verification: `uv run pytest tests/test_server_cli_groceries.py -q`.

10. **Make Meal Generation Inventory-Aware**
    Context: `src/tools/generate_plan.py`, `src/tools/load_saved_meals.py`.
    Build meal candidates from existing hard-coded meal options plus saved meals where category is usable. Rank candidates by inventory coverage, with extra weight for perishables. Prefer complete inventory-covered meals; when incomplete, choose best-fit meals and add missing mapped ingredients to supplemental `grocery_list`.
    Verification: `uv run pytest tests/test_generate_plan_inventory.py -q`.

11. **Track Inventory Usage After Generation**
    Context: `src/tools/generate_plan.py`, `src/tools/grocery_inventory.py`.
    After planning, write `inventory_usage.used`, `inventory_usage.unused`, and `inventory_usage.supplemental`. Do not remove inventory quantities in v1; usage is reporting only.
    Verification: `uv run pytest tests/test_generate_plan_inventory.py::test_generation_records_inventory_usage -q`.

12. **Update API Models For State Compatibility**
    Context: `src/api/models.py`, `src/api/endpoints/state.py`, `src/api/endpoints/meal_plan.py`.
    Add optional inventory fields to `StateResponse` and `UpdateStateRequest`; include `inventory_usage` and confidence metadata in plan/state responses if present. No new grocery API endpoint is required for v1 because the requested interface is CLI.
    Verification: `uv run pytest tests/test_api/test_state.py tests/test_api/test_meal_plan.py -q`.

13. **Document User Flow**
    Context: `README.md`, `.env.example`.
    Document `GEMINI_API_KEY`, grocery commands, the reusable 0-1 confidence scale, `>= 0.7` auto-save behavior, confidence scores in command output, manual macro fallback, and the changed meaning of `grocery_list` when inventory exists.
    Verification: `uv run pytest tests/test_docs_smoke.py -q` or, if no docs smoke test is added, `uv run pytest tests/test_cli_groceries.py -q`.

## Acceptance Scenarios
- Input: "I got two pounds boneless chicken thighs, a tub of Greek yogurt, spinach, and half a pound of salmon."
  Result: each parsed entry displays a `0.0-1.0` confidence score; entries with `confidence_score >= 0.7` save automatically; inventory list shows parsed quantities, CORGIS descriptions, and confidence metadata.
- Input includes an obscure item not in `food.csv`.
  Result: CLI displays the low confidence score or no-match status, prompts for `portion|calories|protein|carbs|fat`, appends it to `specialty-ingredients.md`, then saves it as inventory.
- Generate with enough inventory for several meals.
  Result: meals prioritize bought perishables; supplemental grocery list only includes missing ingredients.
- Generate with no inventory.
  Result: existing deterministic behavior remains valid and `grocery_list` is still populated.

## Assumptions
- Tests must mock Gemini; no test should require a real `GEMINI_API_KEY`.
- The next agent should avoid full-suite runs until state-mutating tests are isolated, because existing persistence tests can write to tracked `src/state/state.json`.
- v1 does not generate brand-new LLM meal recipes from inventory; it only selects from existing hard-coded and saved meal candidates.
- Confidence is a shared LLM-workflow concept, not a grocery-specific concept. Grocery parsing is only the first consumer.
