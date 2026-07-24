# Supabase Data Schema — Design

**Issue:** [#48 — Define and establish the Supabase data schema](https://github.com/evanmei87/meal-planner/issues/48)
**Date:** 2026-07-23
**Status:** Approved design, pending implementation plan

---

## 1. Context

The app stores all mutable data in local files:

- `src/state/state.json` — plan, grocery list, inventory, preferences, session state
- `src/state/exercise_schedule.json` — dated exercise entries
- `src/state/exercise_presets.json` — day-of-week exercise templates
- `src/state/phrase_cache.json` — LLM grocery-phrase match cache
- `src/data/meal-recipes.md` — saved meals/recipes
- `src/data/specialty-ingredients.md` — manually curated ingredient nutrition
- `src/data/food.csv` — USDA-style nutrition reference
- `src/data/user_stats.csv` — height/weight/age/gender

Nothing is user-scoped today — the app is single-tenant with no auth. This design establishes the target Supabase/Postgres schema **only**. Data migration and switching FastAPI to read/write Supabase happen in follow-up per-domain issues (§7).

The app will have exactly one user (the owner). We still model `owner_id` and RLS properly now, because it is cheap with one user and avoids a schema rewrite if multi-user auth is added later.

## 2. Goals & Scope

**In scope (this issue):**

- Version-controlled Supabase migrations under `supabase/migrations/` creating the full schema: tables, keys, relationships, indexes, timestamps, triggers, and baseline RLS.
- One seeded Supabase Auth user; all user-owned tables reference `auth.users(id)`.
- Schema documentation (table purposes, relationships, ownership, local-source mapping).
- A documented, repeatable process for future schema changes.
- Filing the six follow-up implementation issues (§7) on GitHub.

**Out of scope (this issue):**

- Migrating existing local data into Supabase.
- Replacing JSON/Markdown/CSV storage code; changing FastAPI endpoints, tools, or frontend queries.
- Implementing auth/login flows beyond the schema/RLS prerequisites.
- `phrase_cache.json` — stays a local performance cache (see §6).

## 3. Architecture & Tooling

- **Supabase CLI** linked to the existing (currently unlinked) hosted project via `supabase link`.
- **Local validation:** `supabase start` runs Postgres in Docker. Every migration is applied and sanity-checked locally with `supabase db reset` before `supabase db push` to the hosted project.
- **Migrations:** one file per logical change under `supabase/migrations/`, timestamp-prefixed (CLI convention). This *is* the repeatable change process: new migration → `supabase db reset` locally → review → `supabase db push`.
- **`supabase/config.toml`** (non-secret project ref) is committed. Secrets are not (see §4).
- **Auth seed:** one Supabase Auth user is created (dashboard or CLI). Its UUID becomes the `DEFAULT` for `owner_id` columns so the future data migration lands under the correct owner without app-level auth wiring.
- **Docs:** `supabase/README.md` covers the ERD/table reference and the "how to add or change a table" process.

## 4. Security (public repository)

This is a **public repo**, so secret handling is explicit.

**Never committed** (kept in `.env`, already gitignored, read like the existing `GEMINI_API_KEY`):

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` — bypasses RLS; full read/write. Server-side only.
- Supabase CLI access token / DB password (used only for `link`/`push`).

`.env.example` (committed, no real values) documents the required variable names.

**Backend ↔ Supabase access model:** FastAPI is already the trusted gatekeeper (every route sits behind `X-API-Key`). The backend authenticates to Supabase with the `service_role` key and filters every query by the single `owner_id` in code. RLS policies still exist (acceptance criterion, defense-in-depth, and immediately meaningful if multi-user auth is added), but they are not the primary access-control path today.

**Hardening:**

- Enable RLS on every user-owned table with `FORCE ROW LEVEL SECURITY` and a **default-deny** posture (no matching policy ⇒ no access). A leaked `anon` key then exposes nothing.
- The frontend (`web/`) never talks to Supabase directly — it calls FastAPI only. No Supabase credentials belong in `web/.env`.

**Related fix already applied this session (separate from the schema):** the API key gate previously fell back to a hardcoded literal (`dev-key-change-in-production`) committed to the public repo, and the local `.env` was literally using that value. The key was rotated, and `src/api/main.py` / `src/server.py` now refuse to start if `MEAL_PLANNER_API_KEY` is unset instead of defaulting to a known string. Docs and `.env.example` no longer instruct using the placeholder as a real key.

## 5. Schema

15 tables across six domains. Conventions unless noted:

- UUID primary keys (`gen_random_uuid()`).
- User-owned tables carry `owner_id uuid NOT NULL REFERENCES auth.users(id) DEFAULT '<seeded-user-uuid>'`, `created_at timestamptz NOT NULL DEFAULT now()`, `updated_at timestamptz NOT NULL DEFAULT now()`.
- A shared `set_updated_at()` trigger maintains `updated_at`.
- RLS: `FORCE ROW LEVEL SECURITY`, default-deny, one policy per command scoped `owner_id = auth.uid()`.
- Index on `owner_id` (and other columns noted per table).

### 5.1 Profile, stats, preferences

**`profiles`** — 1:1 with `auth.users`.
- `id uuid PK REFERENCES auth.users(id)`, `created_at`, `updated_at`.

**`user_stats`** — TDEE inputs, one row per user (no history, matching today).
- `owner_id`, `height_cm numeric`, `weight_kg numeric`, `age int`, `gender text`, timestamps.

**`user_preferences`** — one row per user.
- `owner_id`, `preferences_text text`, `normalized_exclusions text[]`, timestamps.

### 5.2 Food reference

**`usda_foods`** — static nutrition reference, **not** user-owned. Wide table mirroring `food.csv` one column per nutrient (~34 numeric columns). No EAV model.
- `nutrient_data_bank_number text PK`, `category text`, `description text`, plus nutrient columns (`carbohydrate`, `protein`, `total_fat`, `sodium`, … `numeric`).
- RLS enabled; `SELECT` allowed to the authenticated role. Writes only via migration / `service_role`.
- Index on `category`, `description` for lookup.

### 5.3 Saved meals

**`meals`** — reusable meal definitions (from `meal-recipes.md`).
- `id PK`, `owner_id`, `name text`, `version text`, `category text`, `servings int`, meal-level totals `calories int`, `protein int`, `carbs int`, `fat int`, timestamps.

**`meal_ingredients`** — ordered structured ingredients. Per-ingredient macros are independent estimates and are **not** constrained to sum to the meal totals (known behavior, #45).
- `id PK`, `meal_id FK REFERENCES meals(id) ON DELETE CASCADE`, `name text`, `serving text`, `calories int`, `protein int`, `carbs int`, `fat int`, `position int`.
- Index on `meal_id`.

**`meal_instructions`** — ordered steps.
- `id PK`, `meal_id FK ON DELETE CASCADE`, `step_order int`, `text text`.
- Index on `meal_id`.

**`meal_tags`** — tags as queryable rows.
- `meal_id FK ON DELETE CASCADE`, `tag text`, PK `(meal_id, tag)`.

### 5.4 Meal plans

Plan meals are **snapshots**, decoupled from saved meals: editing or deleting a saved meal must not rewrite or break an existing plan, and the plan already stores a lossy simplified form of a meal (ingredients as text, not structured rows).

**`meal_plans`** — a generated plan.
- `id PK`, `owner_id`, `plan_id text` (legacy identifier continuity, nullable), `current_day text`, `inventory_usage jsonb` (used/unused/supplemental snapshot from generation), timestamps.

**`meal_plan_meals`** — snapshot of a meal within a plan day. Day grouping is a column; day totals are derived (`SUM`), not stored — this replaces the issue's proposed `meal_plan_days` table.
- `id PK`, `meal_plan_id FK ON DELETE CASCADE`, `day text`, `position int`, `name text`, `calories int`, `protein int`, `carbs int`, `fat int`, `ingredients jsonb` (string array), `meal_id uuid NULL REFERENCES meals(id) ON DELETE SET NULL` (provenance only).
- Index on `(meal_plan_id, day, position)`.

**`meal_plan_grocery_items`** — the plan's computed grocery list (ingredients needed minus inventory). Not a reference to any other table's rows — genuinely new per-plan output.
- `id PK`, `meal_plan_id FK ON DELETE CASCADE`, `item text`, `quantity numeric`, `unit text`, `category text`.
- Index on `meal_plan_id`.

### 5.5 Grocery inventory

**`grocery_inventory_items`** — items on hand. Matched and unmatched items share one table; "unmatched" is simply `nutrient_data_bank_number IS NULL` (replaces the issue's separate `unmatched_grocery_items` table). The `inventory_usage` snapshot lives on `meal_plans.inventory_usage` (jsonb), not its own table.
- `id PK`, `owner_id`, `raw_phrase text`, `standardized_item text`, `unit text`, `quantity numeric`, `category text`.
- Match fields (nullable): `nutrient_data_bank_number text REFERENCES usda_foods(nutrient_data_bank_number)`, `corgis_description text`, `corgis_category text`, `corgis_style_query text`, `confidence_score numeric`, `confidence_level text`, `should_auto_save boolean`, `source text`.
- Timestamps. Index on `owner_id`, and on `nutrient_data_bank_number`.

### 5.6 Exercise scheduling

**`exercises`** — dated exercise entries (from `exercise_schedule.json`, whose date-keyed dict becomes a real `date` column).
- `id PK`, `owner_id`, `date date`, `day_name text`, `type text` (CHECK in `running|walking|biking|swimming|strength`), `distance_miles numeric NULL`, `duration_minutes numeric`, `sets int NULL`, `reps int NULL`, `calories int`, `notes text NULL`, `position int`, timestamps.
- Index on `(owner_id, date)`.

**`exercise_presets`** — one reusable template per weekday.
- `id PK`, `owner_id`, `day_of_week text` (CHECK Monday–Sunday), timestamps. Unique `(owner_id, day_of_week)`.

**`exercise_preset_items`** — ordered items within a preset.
- `id PK`, `preset_id FK REFERENCES exercise_presets(id) ON DELETE CASCADE`, `type text` (same CHECK), `distance_miles numeric NULL`, `duration_minutes numeric`, `sets int NULL`, `reps int NULL`, `notes text NULL`, `position int`.
- Index on `preset_id`.

No FK links a scheduled `exercises` row back to the preset it came from — presets are stamped then independent, matching current behavior.

## 6. Local storage → target mapping

| Local source | Target | Notes |
| --- | --- | --- |
| `src/state/state.json` → plan/grocery | `meal_plans`, `meal_plan_meals`, `meal_plan_grocery_items` | Meals embedded as snapshots. |
| `src/state/state.json` → inventory / unmatched / usage | `grocery_inventory_items`, `meal_plans.inventory_usage` | Matched + unmatched unified; usage as jsonb. |
| `src/state/state.json` → preferences | `user_preferences` | `preferences_text` + `normalized_exclusions`. |
| `src/state/exercise_schedule.json` | `exercises` | Date-keyed dict → `date` column. |
| `src/state/exercise_presets.json` | `exercise_presets`, `exercise_preset_items` | Keyed by weekday. |
| `src/state/phrase_cache.json` | — | Out of scope; stays a local performance cache (algorithm-version-invalidated). |
| `src/data/meal-recipes.md` | `meals`, `meal_ingredients`, `meal_instructions`, `meal_tags` | |
| `src/data/specialty-ingredients.md` | `usda_foods` (or an adjacent reference row set) | Fallback nutrition; folded into food reference domain. |
| `src/data/food.csv` | `usda_foods` | |
| `src/data/user_stats.csv` | `user_stats` | Single row. |

## 7. Follow-up implementation issues (to be filed on GitHub)

Cutover is **per-domain, straight cutover** (migrate that domain's data → switch code reads/writes to Supabase → delete the dead local file; no dual-write). Filed as part of this work.

| # | Domain issue | Migrates | Deletes on cutover |
| --- | --- | --- | --- |
| 1 | **Food reference** (+ Supabase client scaffolding in FastAPI) | `food.csv`, `specialty-ingredients.md` → `usda_foods` | `food.csv`, `specialty-ingredients.md` |
| 2 | **Saved meals** | `meal-recipes.md` → `meals` + children | `meal-recipes.md` |
| 3 | **Profile / stats / preferences** | `user_stats.csv` + prefs in `state.json` → `profiles`, `user_stats`, `user_preferences` | `user_stats.csv` |
| 4 | **Meal plans + grocery list** | plan/grocery in `state.json` → `meal_plans`, `meal_plan_meals`, `meal_plan_grocery_items` | (part of `state.json`) |
| 5 | **Grocery inventory** | inventory in `state.json` → `grocery_inventory_items` | (part of `state.json`) |
| 6 | **Exercises + presets** | `exercise_schedule.json`, `exercise_presets.json` → `exercises`, `exercise_presets`, `exercise_preset_items` | both JSON files |

**Order rationale:** food reference first (meals reference it; it carries the shared Supabase-client scaffolding). Meals before plans (plans reference meals for provenance). Plans/inventory/exercises are independent leaves after. `state.json` is deleted only once issues 3–5 have drained it.

Issue #1 also stands up the shared Supabase client in FastAPI (`service_role` key from `.env`, a thin `src/db/` accessor, in-code `owner_id` filtering), since the per-domain approach has no separate infra issue.

## 8. Deliverables

- `supabase/` initialized and linked; `config.toml` committed.
- Migration(s) under `supabase/migrations/` creating the §5 schema — tables, keys, relationships, indexes, timestamps, `set_updated_at()` trigger, and RLS policies.
- One seeded Supabase Auth user; migrations validated locally (`supabase db reset`) and applied to the hosted project (`supabase db push`).
- `supabase/README.md` — table reference, ownership rules, local-source mapping (§6), and the add/change-a-table process (§3).
- Six follow-up issues (§7) filed on GitHub.
- No application code switched from local storage to Supabase in this issue.

## 9. Acceptance criteria

- [ ] Persistent domains documented and mapped to Supabase tables (§5, §6).
- [ ] Initial schema represented by version-controlled migrations in `supabase/migrations/`.
- [ ] Migrations create the agreed tables, keys, relationships, timestamps, indexes, and baseline RLS.
- [ ] Migrations validated locally and applied to the linked hosted project.
- [ ] User-owned data structured for Supabase Auth and protected with default-deny RLS.
- [ ] Schema documentation identifies each table's purpose, relationships, and the local source it will replace.
- [ ] Documentation explains how contributors add/modify tables through new, tested migrations (local validation + deploy steps).
- [ ] No application code is switched from local storage to Supabase in this issue.
- [ ] The six follow-up implementation issues are filed on GitHub.
