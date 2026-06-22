# Improved Preferences UI — Design Spec

**Issue:** [#5 feat: improved preferences ui](https://github.com/evanmei87/meal-planner/issues/5)
**Date:** 2026-06-22
**Branch:** feat/5-preferences-enhance

---

## Problem

The `preferences` field on the Plan page is transient — it is sent with plan generation but never persisted. As a result:
- The input is blank every time the user visits the Plan page.
- The State page has no visibility into what preferences shaped the current plan.
- There is no way to update preferences without navigating back to the Plan page and regenerating.

---

## Goals

1. Add a helpful placeholder/example to the Plan page preferences input.
2. Persist preferences in `state.json` so they survive page reloads.
3. Show and edit preferences on the State page.
4. Allow regenerating the current plan from the State page using stored preferences.

---

## Out of Scope

- Per-day preferences.
- Multi-user / profile support.
- Preferences history or versioning.

---

## Approach

Store `preferences` as a top-level string field in the existing `state.json` file, read and written through the existing `GET /state/` and `PUT /state/` endpoints. No new endpoints or files.

---

## Backend Changes

### `src/api/models.py`

- Add `preferences: Optional[str] = None` to `StateResponse`.
- Add `preferences: Optional[str] = None` to `UpdateStateRequest`.

### `src/api/endpoints/state.py`

- `GET /state/`: read `state.get('preferences')` and include it in `StateResponse`.
- `PUT /state/`: if `request.preferences is not None`, include it in `update_data`.

### `src/state/state.json`

Gains a `preferences` key on first save. Absent/`null` is treated as an empty string on the frontend.

### API Documentation

- Update the `GET /state/` and `PUT /state/` docstrings to document the new `preferences` field.
- Include sample curl calls in the pull request description (see PR section below).

---

## Frontend Changes

### `web/src/api/types.ts`

- Add `preferences?: string` to the `AppState` interface.

### `web/src/api/client.ts`

- Add `state.update(body: Partial<AppState>)` method that calls `PUT /state/` with a JSON body.

### Plan page — `web/src/features/plan/PlanPage.tsx`

- Set the preferences `<input>` placeholder to `"e.g. no red meat, high protein, vegetarian lunches"`.
- On mount, call `useAppState` and pre-fill the `preferences` local state with `state.preferences ?? ''`.
- After a successful `generate.mutate(...)`, call `api.state.update({ preferences })` to persist the value.

### State page — `web/src/features/state/StatePage.tsx`

Add a **Preferences** section at the top of the page:

```
Preferences
[__________________________________] [Save]

[Regenerate Plan]   ← visible only when plan_id is non-empty
```

- The input is initialised from `state.preferences`.
- "Save" calls `PUT /state/` with the edited preferences string, then invalidates the `['state']` query.
- "Regenerate Plan" calls `POST /plan/generate` with the stored preferences, then invalidates `['state']` and `['plan']`.

### `web/src/features/state/hooks.ts`

- Add `useUpdateState` mutation hook (calls `api.state.update`).

---

## Testing

### Plan page (`web/src/features/plan/PlanPage.test.tsx`)

- Pre-fill: when the state fixture includes `preferences: "high protein"`, the input renders with that value.
- Persist on generate: after a successful generation, `PUT /state/` is called with the current preferences value.

### State page (`web/src/features/state/StatePage.test.tsx`)

- Preferences input renders with the stored value from the state fixture.
- "Save" button triggers `PUT /state/` with the edited value.
- "Regenerate Plan" button is visible when `plan_id` is non-empty.
- "Regenerate Plan" button is absent when `plan_id` is `''`.
- Clicking "Regenerate Plan" calls `POST /plan/generate` with the stored preferences.

---

## Acceptance Criteria

- [ ] Preferences input on Plan page has an example placeholder.
- [ ] Stored preferences pre-fill the Plan page input on load.
- [ ] Generating a plan persists the entered preferences to state.
- [ ] State page shows a Preferences section with an editable input.
- [ ] Saving from the State page updates `state.json` via `PUT /state/`.
- [ ] "Regenerate Plan" button appears on State page only when a plan exists.
- [ ] Clicking "Regenerate Plan" calls `POST /plan/generate` with stored preferences and refreshes state.
- [ ] `GET /state/` and `PUT /state/` docstrings document the `preferences` field.
- [ ] PR description includes sample curl calls for `GET /state/` and `PUT /state/` with `preferences`.
- [ ] All new behaviour is covered by frontend tests.

---

## Sample Curl Calls (for PR)

```bash
# Read current state (includes preferences)
curl -s -H "X-API-Key: $API_KEY" http://localhost:8000/api/state/ | jq .preferences

# Save preferences
curl -s -X PUT http://localhost:8000/api/state/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"preferences": "high protein, no red meat"}' | jq .preferences

# Regenerate plan using stored preferences
curl -s -X POST http://localhost:8000/api/plan/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"preferences": "high protein, no red meat"}' | jq .status
```
