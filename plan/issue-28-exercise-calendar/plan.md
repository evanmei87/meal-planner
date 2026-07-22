# Weekly Calendar View — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> Originating issue: [#28 — Weekly calendar view with EST current-day indicator](https://github.com/evanmei87/meal-planner/issues/28)
> Design spec: [`docs/superpowers/specs/2026-07-19-exercise-calendar-view-design.md`](../../docs/superpowers/specs/2026-07-19-exercise-calendar-view-design.md)

**Goal:** Add a fifth "Exercise" tab showing the current week (Mon–Sun) as a row of clickable day cells, with today (in `America/New_York`) visually highlighted. UI shell only — no exercise data, no backend changes.

**Architecture:** Two new files under `web/src/features/exercise/` — a pure date-math module (`dateUtils.ts`) and a presentational page component (`ExerciseCalendarPage.tsx`) built from the existing shared `Card` and `Button` components. Two existing files get a small, additive change each (`App.tsx` nav link, `main.tsx` route). No API calls, no new dependencies, no backend touch.

**Tech Stack:** React 18 + TypeScript, Vite, Tailwind v4 + shadcn/Base UI (`Card`, `Button`), Vitest + Testing Library.

## Global Constraints

- No date library (date-fns/dayjs) — use native `Date`/`Intl` only (issue #28 explicitly forbids adding one).
- "Today" is computed in `America/New_York` regardless of the visitor's local timezone.
- `web/src/features/exercise/ExerciseCalendarPage.tsx` is inside the design-system gate's scope (`web/src/features/*/*.tsx`) — it must introduce **zero** new raw Tailwind palette classes (`bg-green-600`, etc.) and **zero** bare `<button>` tags, per `.design-sync/north-star.md` invariants 1 and 2. All color must come from semantic tokens (`bg-primary`, `text-primary-foreground`, `text-muted-foreground`, etc.) via the shared `Button`/`Card` components.
- The today-highlight uses `bg-primary text-primary-foreground` (via `Button variant="default"`) per `docs/design-tokens.md`, **not** the issue body's literal `bg-green-600 text-white` example.
- Plan files under `plan/` are always committed to git (per `CLAUDE.md`); stage and commit everything under `plan/` before opening the PR.
- Run `npm test -- --run` from `web/` before considering any task done.
- Branch: `feat/28-exercise-calendar-shell`. Base branch for PR: `main`.

---

### Task 1: `dateUtils.ts` — EST date math

**Files:**
- Create: `web/src/features/exercise/dateUtils.ts`
- Test: `web/src/features/exercise/dateUtils.test.ts`

**Interfaces:**
- Consumes: nothing (pure functions, only the built-in `Date`/`Intl`).
- Produces:
  - `getTodayInEST(): string` — today's date as `YYYY-MM-DD` in `America/New_York`.
  - `getCurrentWeekDates(referenceISODate?: string): { date: string; dayName: string }[]` — always exactly 7 entries, Monday first, Sunday last. `date` is `YYYY-MM-DD`; `dayName` is the full English weekday name (e.g. `"Monday"`). Defaults `referenceISODate` to `getTodayInEST()`.

- [ ] **Step 1: Write the failing tests**

Create `web/src/features/exercise/dateUtils.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from 'vitest'
import { getTodayInEST, getCurrentWeekDates } from './dateUtils'

afterEach(() => {
  vi.useRealTimers()
})

describe('getTodayInEST', () => {
  it('returns the date in America/New_York as YYYY-MM-DD', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-24T12:00:00-04:00'))
    expect(getTodayInEST()).toBe('2026-06-24')
  })

  it('resolves to the previous EST day when UTC has already rolled over', () => {
    // 2026-06-25T02:00:00Z is 2026-06-24T22:00:00 in New York (EDT, UTC-4) — still the 24th locally.
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-25T02:00:00Z'))
    expect(getTodayInEST()).toBe('2026-06-24')
  })
})

describe('getCurrentWeekDates', () => {
  it('returns Monday through Sunday for a Wednesday reference date', () => {
    const week = getCurrentWeekDates('2026-06-24') // a Wednesday
    expect(week).toEqual([
      { date: '2026-06-22', dayName: 'Monday' },
      { date: '2026-06-23', dayName: 'Tuesday' },
      { date: '2026-06-24', dayName: 'Wednesday' },
      { date: '2026-06-25', dayName: 'Thursday' },
      { date: '2026-06-26', dayName: 'Friday' },
      { date: '2026-06-27', dayName: 'Saturday' },
      { date: '2026-06-28', dayName: 'Sunday' },
    ])
  })

  it('returns the same week when the reference date is a Sunday', () => {
    const week = getCurrentWeekDates('2026-06-28') // a Sunday
    expect(week[0].date).toBe('2026-06-22')
    expect(week[6].date).toBe('2026-06-28')
  })

  it('defaults to the week containing today in EST when no reference date is given', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-24T12:00:00-04:00'))
    const week = getCurrentWeekDates()
    expect(week[2].date).toBe('2026-06-24')
    expect(week[2].dayName).toBe('Wednesday')
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (from `web/`): `npm test -- --run dateUtils`
Expected: FAIL — `dateUtils.ts` does not exist yet (`Cannot find module './dateUtils'`).

- [ ] **Step 3: Implement `dateUtils.ts`**

Create `web/src/features/exercise/dateUtils.ts`:

```ts
export function getTodayInEST(): string {
  return new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' })
}

export function getCurrentWeekDates(
  referenceISODate: string = getTodayInEST()
): { date: string; dayName: string }[] {
  const reference = new Date(`${referenceISODate}T00:00:00`)
  const daysSinceMonday = (reference.getDay() + 6) % 7
  const monday = new Date(reference)
  monday.setDate(reference.getDate() - daysSinceMonday)

  return Array.from({ length: 7 }, (_, i) => {
    const day = new Date(monday)
    day.setDate(monday.getDate() + i)
    return {
      date: day.toLocaleDateString('en-CA'),
      dayName: day.toLocaleDateString('en-US', { weekday: 'long' }),
    }
  })
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test -- --run dateUtils`
Expected: PASS — all 5 tests green.

- [ ] **Step 5: Commit**

```bash
git add web/src/features/exercise/dateUtils.ts web/src/features/exercise/dateUtils.test.ts
git commit -m "feat: add EST week date utilities for exercise calendar (#28)"
```

---

### Task 2: `ExerciseCalendarPage.tsx` — calendar UI

**Files:**
- Create: `web/src/features/exercise/ExerciseCalendarPage.tsx`
- Test: `web/src/features/exercise/ExerciseCalendarPage.test.tsx`

**Interfaces:**
- Consumes: `getTodayInEST()`, `getCurrentWeekDates()` from `./dateUtils` (Task 1); `Card` from `@/components/Card`; `Button` from `@/components/ui/button`.
- Produces: `ExerciseCalendarPage()` — a React component, default-exported as a named export `ExerciseCalendarPage`, no props. Consumed by Task 3 (`main.tsx` route).

- [ ] **Step 1: Write the failing tests**

Create `web/src/features/exercise/ExerciseCalendarPage.test.tsx`:

```tsx
import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ExerciseCalendarPage } from './ExerciseCalendarPage'

describe('ExerciseCalendarPage', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-06-24T12:00:00-04:00')) // a Wednesday
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders all 7 days of the current week', () => {
    render(<ExerciseCalendarPage />)
    expect(screen.getAllByRole('button')).toHaveLength(7)
    expect(screen.getByRole('button', { name: 'Mon, Jun 22' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sun, Jun 28' })).toBeInTheDocument()
  })

  it('highlights today with the primary token', () => {
    render(<ExerciseCalendarPage />)
    const today = screen.getByRole('button', { name: 'Wed, Jun 24' })
    expect(today.className).toContain('bg-primary')

    const notToday = screen.getByRole('button', { name: 'Mon, Jun 22' })
    expect(notToday.className).not.toContain('bg-primary')
  })

  it('shows a placeholder for today by default', () => {
    render(<ExerciseCalendarPage />)
    expect(screen.getByText('Exercises for 2026-06-24')).toBeInTheDocument()
  })

  it('updates the placeholder when a different day is clicked', () => {
    render(<ExerciseCalendarPage />)
    fireEvent.click(screen.getByRole('button', { name: 'Mon, Jun 22' }))
    expect(screen.getByText('Exercises for 2026-06-22')).toBeInTheDocument()
    expect(screen.queryByText('Exercises for 2026-06-24')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test -- --run ExerciseCalendarPage`
Expected: FAIL — `Cannot find module './ExerciseCalendarPage'`.

- [ ] **Step 3: Implement `ExerciseCalendarPage.tsx`**

Create `web/src/features/exercise/ExerciseCalendarPage.tsx`:

```tsx
import { useState } from 'react'
import { Card } from '@/components/Card'
import { Button } from '@/components/ui/button'
import { getTodayInEST, getCurrentWeekDates } from '@/features/exercise/dateUtils'

function formatShortDate(date: string): string {
  return new Date(`${date}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}

export function ExerciseCalendarPage() {
  const today = getTodayInEST()
  const week = getCurrentWeekDates()
  const [selectedDate, setSelectedDate] = useState(today)

  return (
    <div>
      <div className="flex gap-2 mb-4 flex-wrap">
        {week.map((day) => (
          <Card key={day.date}>
            <Button
              variant={day.date === today ? 'default' : 'ghost'}
              onClick={() => setSelectedDate(day.date)}
            >
              {day.dayName.slice(0, 3)}, {formatShortDate(day.date)}
            </Button>
          </Card>
        ))}
      </div>
      <p className="text-sm text-muted-foreground">Exercises for {selectedDate}</p>
    </div>
  )
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test -- --run ExerciseCalendarPage`
Expected: PASS — all 4 tests green.

- [ ] **Step 5: Run the design-system gate against this file**

Run (from repo root): `node .design-sync/check/ds-check.mjs`
Expected: `no-raw-palette` and `no-bare-button` counts unchanged from before this task (`ExerciseCalendarPage.tsx` contributes 0 to both — it uses only `Button`/`Card` and semantic-token classes).

- [ ] **Step 6: Commit**

```bash
git add web/src/features/exercise/ExerciseCalendarPage.tsx web/src/features/exercise/ExerciseCalendarPage.test.tsx
git commit -m "feat: add exercise calendar page shell (#28)"
```

---

### Task 3: Wire up nav link and route

**Files:**
- Modify: `web/src/App.tsx`
- Modify: `web/src/main.tsx`

**Interfaces:**
- Consumes: `ExerciseCalendarPage` from `@/features/exercise/ExerciseCalendarPage` (Task 2).
- Produces: route `/exercise` reachable from the app shell; nothing downstream depends on this task.

- [ ] **Step 1: Add the nav link in `App.tsx`**

In `web/src/App.tsx`, insert a new `NavLink` immediately after the existing "Plan" link (before "Meals"):

```tsx
<NavLink
  to="/exercise"
  className={({ isActive }) =>
    isActive ? 'text-green-600' : 'text-gray-600 hover:text-green-600'
  }
>
  Exercise
</NavLink>
```

(Matches the three existing `NavLink`s' classes exactly — this file is outside the design-system gate's scope, and migrating the nav's active-state color to a token is a separate, later change per `docs/design-tokens.md`.)

- [ ] **Step 2: Add the route in `main.tsx`**

In `web/src/main.tsx`, add the import next to the other feature-page imports:

```tsx
import { ExerciseCalendarPage } from '@/features/exercise/ExerciseCalendarPage'
```

And add the route inside `<Routes>`, after the `plan` route:

```tsx
<Route path="exercise" element={<ExerciseCalendarPage />} />
```

- [ ] **Step 3: Run the full frontend test suite**

Run (from `web/`): `npm test -- --run`
Expected: PASS — all existing tests plus the 9 new ones from Tasks 1–2 are green.

- [ ] **Step 4: Type-check**

Run (from `web/`): `npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 5: Manual browser check**

Start both servers (`uv run uvicorn src.api.main:app --reload` from repo root, `npm run dev` from `web/`) and visit `http://localhost:5173/exercise`. Confirm:
- Nav bar shows Plan, Exercise, Meals, Groceries, State in that order, and "Exercise" highlights when active.
- The current week renders as 7 cells; today's cell is visually distinct (primary color).
- Clicking a different cell updates the "Exercises for {date}" text below the row.

- [ ] **Step 6: Commit**

```bash
git add web/src/App.tsx web/src/main.tsx
git commit -m "feat: wire up exercise route and nav link (#28)"
```

---

### Task 4: Design-system review, plan file, and PR

**Files:**
- Verify: `.design-sync/check/baseline.json` (should be unchanged — no ratchet expected, since Task 2 introduced 0 new violations).
- Commit: `plan/issue-28-exercise-calendar/plan.md` (this file).

**Interfaces:**
- Consumes: the full diff from Tasks 1–3.
- Produces: an open PR against `main`.

- [ ] **Step 1: Run the design-system gate**

Run (from repo root): `node .design-sync/check/ds-check.mjs --gate`
Expected: exits 0. If it reports a regression, the localized file:line output points at the new violation — fix it (most likely cause: a raw Tailwind color class or a bare `<button>` slipped into `ExerciseCalendarPage.tsx`) before continuing.

- [ ] **Step 2: Offer the Tier 2 design review**

This change adds new `className` usage in `web/src/features/exercise/ExerciseCalendarPage.tsx`, so the Stop hook will report Tier 2 review as stale. Per `CLAUDE.md`, offer `/ds-review` to the user at this point (needs both dev servers and a browser session) rather than running it unprompted or skipping it.

- [ ] **Step 3: Commit the plan file**

```bash
git add plan/issue-28-exercise-calendar/plan.md
git commit -m "docs: add implementation plan for exercise calendar (#28)"
```

- [ ] **Step 4: Request code review**

Use the `superpowers:requesting-code-review` skill against the full branch diff before opening the PR.

- [ ] **Step 5: Push and open the PR**

```bash
git push -u origin feat/28-exercise-calendar-shell
```

Open the PR with `gh pr create`, and include in the PR body:
- A link to issue #28 and to the design spec (`docs/superpowers/specs/2026-07-19-exercise-calendar-view-design.md`).
- The actual terminal output (not a paraphrase) from `npm test -- --run`, `npx tsc --noEmit`, and `node .design-sync/check/ds-check.mjs --gate` run at the tip of the branch, as validation proof.
- A summary of what was verified manually in Step 5 of Task 3 (nav order, today-highlight, click-to-update placeholder).

---

## Self-Review Notes

- **Spec coverage:** §4.1 → Task 1. §4.2 → Task 2. §4.3 → Task 3. §5 (testing) → Tasks 1–2 test steps. §6 risks (gate regression, Tier 2 staleness, novel Card+Button pattern) → Task 4 Steps 1–2 and Task 3 Step 5's manual check.
- **Type consistency:** `getCurrentWeekDates` returns `{ date: string; dayName: string }[]` in Task 1 and Task 2 consumes exactly that shape (`day.date`, `day.dayName`) with no separate type declared — matches the AC's literal signature, no drift.
- **No placeholders:** all steps carry complete, runnable code; no "add tests for the above" or "similar to Task N" shortcuts.
