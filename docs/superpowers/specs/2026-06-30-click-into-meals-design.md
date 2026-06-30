# Design: Click into meals — detail overlay, macro tiles, servings + richer recipes

> Spec for [issue #6 — feat: click into meals](https://github.com/evanmei87/meal-planner/issues/6).
> Date: 2026-06-30 · Status: approved design, ready for implementation plan
> Builds on the shadcn/ui (Base UI) + design-token foundation from [issue #41](https://github.com/evanmei87/meal-planner/issues/41).

## 1. Goal

Make the Meals list rows clickable to open a meal **detail** showing macros, recommended servings, ingredients, and step-by-step instructions — built on the #41 design-token foundation. Add a meal-level **`servings`** field to the data and enrich the five existing recipes with real step-by-step instructions.

This is deliberately scoped to **meal-level** nutrition. Per-ingredient serving sizes and per-ingredient macros (the literal "macros of the ingredients and the serving sizes" in the issue body) are larger — they require restructuring `ingredients` from names into objects — and move to a **follow-up issue** created with this work.

## 2. Decisions (locked during brainstorming)

| Decision | Choice | Consequence |
|---|---|---|
| Nutrition granularity | **Meal-level only** | `ingredients` stays `List[str]`. Per-ingredient macros + serving sizes deferred to a follow-up issue. Keeps this change additive, no data migration of ingredient rows. |
| "Recommended serving sizes" | **Add a meal-level `servings` field** (integer yield) | Displayed macros are labeled **per serving**. Small additive schema change; the 5 existing meals get `servings` filled in. |
| Detail presentation | **Dialog on the list + keep the `/meals/:name` page** | Row click opens an overlay; the standalone page stays for Plan-page deep links ([`PlanPage.tsx:104`](../../../web/src/features/plan/PlanPage.tsx)) and direct URLs. Both render the **same** `MealDetail` component — no duplicated rendering. |
| Mobile "Drawer" | **One responsive Dialog** (centered desktop / bottom-sheet mobile via tokens), not `vaul` | Satisfies the issue's Dialog/Drawer intent with a single component and no extra dependency outside the Base UI / shadcn system. |
| Macro breakdown | **No charting library** — token `StatTile`s + a CSS stacked P/C/F ratio bar | `@tremor/react` targets Tailwind 3 (JS-config theming + Headless UI) and does not cleanly fit Tailwind 4 + Base UI. For 4 numbers + one ratio, tokens + divs is the shadcn idiom. Real charts (and the proper Tailwind-4 replacement, **shadcn Charts / Recharts**) are deferred to #42. |
| Detail data source | **Reuse list/search response; no new `GET /meals/{name}`** | List and search already return full meal objects (instructions, tags). The Dialog uses the clicked row; the page uses the existing `useMeals()` list. The endpoint suggested in the issue's plan comment is unnecessary. |

## 3. Scope

**In scope**
- Add a `servings` column to [`meal-recipes.md`](../../../src/data/meal-recipes.md); fill it for the 5 existing meals and expand their `instructions` into `;`-separated steps.
- Add `servings` to `MealResponse` and `AddMealRequest` ([`src/api/models.py`](../../../src/api/models.py)); thread it through `add_saved_meal`.
- Update **both** recipe parsers to read `servings`, consolidating their duplicated row-parsing onto one shared helper (see §4.1).
- Make Meals-list rows clickable to open `MealDetailDialog`.
- Extract the detail body into a shared `MealDetail` component; keep `MealDetailPage` rendering it.
- Macro breakdown: `StatTile` set + CSS stacked ratio bar from design tokens.
- Add the shadcn `dialog` primitive (`npx shadcn add dialog`) under `web/src/components/ui/`.
- One `servings` number input in the add-meal form.
- Tests: backend parse/round-trip of `servings`; frontend row-click → dialog, `MealDetail` rendering, deep-link page still renders.
- Create the structured-ingredients follow-up issue.

**Out of scope**
- Per-ingredient serving sizes and per-ingredient macros (follow-up issue).
- Restructuring `ingredients` away from `List[str]`.
- A `vaul` Drawer; any charting library (Tremor, Recharts/shadcn Charts → #42).
- A `GET /meals/{name}` endpoint.
- Recomputing meal macro totals (existing values are kept; only sanity-checked).
- Plan-generation logic — it scores meals by ingredient-name overlap, which is unchanged.

## 4. Architecture & components

### 4.1 Data format + parsers

[`meal-recipes.md`](../../../src/data/meal-recipes.md) gains a `servings` column. The file is parsed in **two** places with divergent, brittle rules:

- [`load_saved_meals.py:load_saved_meals`](../../../src/tools/load_saved_meals.py) — splits on `|`, filters empties, requires `len(parts) >= 7`, indexes positions 0–6. (API path.)
- [`add_saved_meal.py:load_recipes`](../../../src/tools/add_saved_meal.py) — splits on `|` without filtering, requires `len(parts) == 9`, indexes positions 1–7. Covered by [`tests/test_add_saved_meal.py`](../../../tests/test_add_saved_meal.py).

Because the format is changing, both are updated together and their row-parsing is consolidated into one shared helper (e.g. `parse_recipe_row`) returning the meal dict incl. `servings`. This removes the `>=7` / `==9` divergence rather than adding a third variant. The macro cell format (`cal,prot,carb,fat`) is unchanged; `servings` is its own column.

`add_saved_meal` writes the new column when appending a row, defaulting `servings` to `1` when not provided so older callers keep working.

### 4.2 Models

`MealResponse` and `AddMealRequest` get `servings: int = Field(default=1, ge=1)`. The meal dict returned by the parsers includes `servings`, so `MealResponse(**meal)` keeps working. Frontend `MealResponse`/`AddMealRequest` types in [`web/src/api/types.ts`](../../../web/src/api/types.ts) gain `servings: number`.

### 4.3 Frontend — one detail, two mounts

```
MealDetail (presentational; props: meal)
 ├─ rendered by MealDetailDialog  ← Meals list row click
 └─ rendered by MealDetailPage    ← /meals/:name (deep links, direct URL)
```

- **`MealDetail`** renders: title, category, **"Makes N serving(s)"**, a **per-serving** macro section (`StatTile`s + ratio bar), ingredients list, numbered instructions, tags. Pure, no data fetching.
- **`MealDetailDialog`** wraps `MealDetail` in the shadcn `dialog`. Responsive: centered modal ≥ `sm`, bottom-sheet below `sm`, styled with design tokens.
- **Meals list**: each row gets a button/clickable affordance opening the dialog with that row's meal object (already fully loaded from search/list). Keyboard-accessible (row is a real button or has `role`/`tabIndex` + Enter/Space).
- **`MealDetailPage`** keeps its current data flow (`useMeals()` list + find, plus the `planMeal` location-state branch) but delegates the saved-meal body to `MealDetail`.

### 4.4 Macro tiles + ratio bar

- `StatTile` (small presentational component, tokens only): label + value, used for **Calories**, **Protein**, **Carbs**, **Fat**. Values labeled per serving.
- **Ratio bar**: a single horizontal bar split into protein/carbs/fat segments by gram proportion, each segment a token color, with an accessible label (e.g. `aria-label`/legend). Pure CSS/flex, no library.

## 5. Testing

**Backend**
- Both parsers read `servings` from a sample row; default to `1` when the column is blank/absent.
- `add_saved_meal` round-trip: add a meal with `servings` → reload → `servings` preserved.
- Existing meal/parse tests stay green after the column addition (update fixtures in `test_add_saved_meal.py`).

**Frontend**
- Clicking a Meals-list row opens the dialog showing that meal's name, servings, macros, and steps.
- `MealDetail` renders servings line, the four `StatTile`s, the ratio bar, and numbered instructions for a sample meal.
- `/meals/:name` page still renders for a saved meal and for the `planMeal` branch.
- Row is keyboard-activatable (Enter opens the dialog).

## 6. Follow-up issue

Create after merge: **"Structured ingredients — per-ingredient serving sizes + macros."** Captures restructuring `ingredients` from `List[str]` to objects (`{name, serving, calories, protein, carbs, fat}`), the data migration of `meal-recipes.md`, the parser/model/add-form changes, the per-ingredient table in `MealDetail`, and impact on plan-generation ingredient scoring. References this issue (#6).

## 7. Risks / open notes

- **shadcn `dialog` on Base UI engine** — confirm `npx shadcn add dialog` generates a Base UI dialog under the repo's `components.json`; the responsive bottom-sheet styling is ours to add via tokens.
- **Parser consolidation** is the highest-touch backend change; the existing `test_add_saved_meal.py` suite is the safety net and its fixtures must be updated to the new column count in lockstep.
- Meal macro totals for the 5 recipes are taken as-is; this issue does not verify their nutritional accuracy.
