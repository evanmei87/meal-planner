# Design: Weekly calendar view with EST current-day indicator

> Spec for [issue #28 — Weekly calendar view with EST current-day indicator](https://github.com/evanmei87/meal-planner/issues/28).
> Date: 2026-07-19 · Status: approved design, ready for implementation plan
> Builds on the shadcn/ui (Base UI) + design-token foundation from [issue #41](https://github.com/evanmei87/meal-planner/issues/41).

## 1. Goal

Add a fifth tab, **Exercise**, showing the current week (Monday–Sunday) as a horizontal row of day cells, with the day that is "today" in `America/New_York` visually highlighted. Clicking a cell shows a placeholder ("Exercises for {date}") below the row. This is UI shell only — no exercise data, no add/edit forms, no backend changes (those are later issues, #04 onward).

## 2. Decisions (locked during brainstorming)

| Decision | Choice | Consequence |
|---|---|---|
| Spec of record | The **issue body's** acceptance criteria, not the older first comment on the issue | The comment ("Implementation Plan") predates the issue's 2026-06-26 update and conflicts with it: different route (`/exercises` vs `/exercise`), different file paths (`pages/ExercisePage.tsx` + `components/WeekCalendar.tsx` vs `features/exercise/...`), adds prev/next week navigation, and computes dates via `toISOString()` (see below). The issue body is authoritative. |
| Week navigation | **None** — current week only | Matches the AC exactly (7 cells for the week containing today, no prev/next). Navigation is out of scope for this issue; can be a follow-up if wanted. |
| Today-highlight color | **`bg-primary text-primary-foreground`** (via `Button variant="default"`), not the issue's literal `bg-green-600 text-white` example | [`docs/design-tokens.md`](../../design-tokens.md) already reserves this exact token for #28's today-highlight. The issue's inline example predates that doc section; the doc is the current source of truth. |
| Date arithmetic | Local-timezone `Date` arithmetic (`getDay()`/`setDate()`) on a `T00:00:00`-anchored `Date`, not `toISOString()` | `toISOString()` converts to UTC first, shifting the calendar date whenever local time is behind UTC (true for all US zones) — a real bug against the EST requirement. `getDay()`/`setDate()` operate on the local calendar fields and are DST-safe for this use (no epoch-based day-skipping). |
| Day-cell composition | `Card` (zero padding) wrapping a `Button` that fills it | AC requires `Card` for the cells; the design-system gate forbids bare `<button>` and requires `Button` for anything interactive. `Card` alone isn't clickable/keyboard-accessible, so `Button` is nested inside it as the actual control. |
| Non-today button variant | `ghost`, not `outline` | `outline` draws its own `border-border`, which combined with `Card`'s own border produces a visible double-border a pixel apart. `ghost` has no border of its own, so `Card`'s border is the only one drawn. |
| Initial `selectedDate` | Defaults to `getTodayInEST()` | The placeholder is populated on first render ("Exercises for {today}") rather than blank until a click. |
| Selected-but-not-today styling | None | The AC only calls for a distinct style on the *today* cell. Clicking a non-today cell changes only the placeholder text, not the cell's appearance — avoids inventing an unspecified second visual state. |
| New NavLink styling | Matches its three siblings' existing classes exactly (including their hardcoded `text-green-600`) | `App.tsx` is outside the design-system gate's scope (`web/src/features/*/*.tsx` only). Migrating the nav's active-state color to the `bg-primary` token is tracked separately per `docs/design-tokens.md` ("the nav active link... converge on this token when their issues migrate") — not part of this issue. Matching siblings keeps the nav bar visually and structurally uniform today. |

## 3. Scope

**In scope**
- `web/src/features/exercise/dateUtils.ts` — `getTodayInEST()`, `getCurrentWeekDates(referenceISODate?)`.
- `web/src/features/exercise/ExerciseCalendarPage.tsx` — the page component.
- `web/src/features/exercise/ExerciseCalendarPage.test.tsx` — tests.
- `web/src/App.tsx` — new `NavLink to="/exercise"` after "Plan".
- `web/src/main.tsx` — new route `path="exercise"` → `ExerciseCalendarPage`.

**Out of scope**
- Backend changes, real exercise data, add/edit/remove forms (issues #02–#05).
- Week navigation (prev/next).
- A dedicated `Input`/form primitive (none needed here — no text entry).
- Migrating `App.tsx`'s other NavLinks or `PlanPage.tsx`'s day-selector to design tokens.

## 4. Architecture & components

### 4.1 `dateUtils.ts`

- `getTodayInEST(): string` — `new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' })`, returning `YYYY-MM-DD`.
- `getCurrentWeekDates(referenceISODate = getTodayInEST()): { date: string; dayName: string }[]` — parses `referenceISODate` via `new Date(referenceISODate + 'T00:00:00')` (local midnight, avoids UTC-shift bugs), finds Monday via `(getDay() + 6) % 7` days back, then walks forward 7 days. Each entry's `date` is `en-CA`-formatted (`YYYY-MM-DD`) and `dayName` is the full English weekday name (`en-US`, `{ weekday: 'long' }`).

### 4.2 `ExerciseCalendarPage.tsx`

```tsx
const today = getTodayInEST()
const week = getCurrentWeekDates()
const [selectedDate, setSelectedDate] = useState(today)

<div className="flex gap-2 mb-4 flex-wrap">
  {week.map((day) => (
    <Card key={day.date} className="p-0">
      <Button
        variant={day.date === today ? 'default' : 'ghost'}
        onClick={() => setSelectedDate(day.date)}
        className="w-full flex-col gap-0.5 h-auto py-3"
      >
        <span>{day.dayName.slice(0, 3)}</span>
        <span>{formatShort(day.date)}</span>
      </Button>
    </Card>
  ))}
</div>
<p>Exercises for {selectedDate}</p>
```

`formatShort` is a small local helper defined in `ExerciseCalendarPage.tsx` (not exported from `dateUtils.ts`, which per the AC exports only `getTodayInEST` and `getCurrentWeekDates`). It renders e.g. "Jun 22" (`toLocaleDateString('en-US', { month: 'short', day: 'numeric' })`), combined with the 3-letter weekday to match the AC's "Mon, Jun 22" example. `dateUtils` itself keeps returning the full weekday name, as specified.

### 4.3 Nav & routing

- `App.tsx`: fourth `NavLink` block, copy-pasted from the existing three (same conditional `isActive` classes), pointed at `/exercise`, placed after "Plan".
- `main.tsx`: `<Route path="exercise" element={<ExerciseCalendarPage />} />`, imported alongside the other feature pages.

## 5. Testing

`ExerciseCalendarPage.test.tsx`:
- `vi.useFakeTimers()` + `vi.setSystemTime(new Date('2026-06-24T12:00:00-04:00'))` (a Wednesday) in `beforeEach`; `vi.useRealTimers()` in `afterEach`.
- Renders 7 day cells; the Wednesday cell is identifiable (by accessible role/name) and carries the today styling.
- Clicking a different day's cell updates the "Exercises for {date}" text to that day's date.

No new test dependencies — existing `@testing-library/react` + `vitest` stack.

## 6. Risks / open notes

- **Design-system gate**: `ExerciseCalendarPage.tsx` is in the gated scope (`web/src/features/*/*.tsx`). The `Card`+`Button` composition above is deliberately token-only (no raw Tailwind palette classes, no bare `<button>`) so it doesn't regress `no-raw-palette` / `no-bare-button` counts in `.design-sync/check/baseline.json`.
- **Tier 2 review**: this is new page-level layout under `features/`, so it will make `/ds-review` overdue per the Stop hook. Per `CLAUDE.md`, that review will be offered (not run unprompted) at a natural boundary — before the PR.
- `Card`+`Button` nesting (zero-padding `Card`, `Button` filling it) is a new pattern for this codebase — no existing screen combines them this way. Worth a visual sanity check once running in the browser.
