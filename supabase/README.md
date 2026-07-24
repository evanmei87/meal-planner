# Supabase Schema

The meal planner's persistent data. See the design spec at
`docs/superpowers/specs/2026-07-23-supabase-data-schema-design.md`.

## Conventions

- UUID primary keys (`gen_random_uuid()`).
- User-owned tables: `owner_id uuid` defaulting to `public.default_owner_id()`
  (the single seeded owner), `created_at`/`updated_at`, and a `set_updated_at`
  trigger. RLS is forced and default-deny, scoped to `auth.uid()`.
- Child tables have no `owner_id`; their RLS checks ownership through the parent.
- `usda_foods` is shared reference data: read-only to clients, writable only
  via migrations / the `service_role` key.

## Tables

| Table | Purpose | Replaces (local source) |
| --- | --- | --- |
| `profiles` | 1:1 with `auth.users` | — (new) |
| `user_stats` | Height/weight/age/gender for TDEE | `src/data/user_stats.csv` |
| `user_preferences` | Free-form prefs + normalized exclusions | `preferences` in `src/state/state.json` |
| `usda_foods` | USDA nutrition reference | `src/data/food.csv` (+ `specialty-ingredients.md`) |
| `meals` | Saved meal definitions | `src/data/meal-recipes.md` |
| `meal_ingredients` | Ordered structured ingredients | `meal-recipes.md` (ingredients cell) |
| `meal_instructions` | Ordered steps | `meal-recipes.md` (instructions cell) |
| `meal_tags` | Meal tags | `meal-recipes.md` (tags cell) |
| `meal_plans` | Generated plans + inventory-usage snapshot | `plan` in `src/state/state.json` |
| `meal_plan_meals` | Snapshot of a meal within a plan day | `plan[].meals` in `state.json` |
| `meal_plan_grocery_items` | A plan's computed grocery list | `grocery_list` in `state.json` |
| `grocery_inventory_items` | Items on hand (matched + unmatched) | `grocery_inventory` / `unmatched_groceries` in `state.json` |
| `exercises` | Dated exercise entries | `src/state/exercise_schedule.json` |
| `exercise_presets` | Day-of-week templates | `src/state/exercise_presets.json` |
| `exercise_preset_items` | Ordered items in a preset | `exercise_presets.json` |

`src/state/phrase_cache.json` is intentionally **not** migrated — it stays a
local performance cache.

## Changing the schema

1. `npx supabase migration new <descriptive_name>` — creates a timestamped file
   under `supabase/migrations/`.
2. Write the DDL. Add a matching pgTAP test under `supabase/tests/`.
3. `npx supabase db reset` — applies all migrations to the local Docker DB
   (requires Docker Desktop running). Fails loudly on bad SQL.
4. `npx supabase test db` — runs the pgTAP assertions.
5. Commit the migration and its test together.
6. `npx supabase db push` — applies to the hosted project.
7. `npx supabase migration list` — confirm local and remote match.

Never edit an already-applied migration; always add a new one.
