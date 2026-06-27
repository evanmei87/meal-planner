# Design: shadcn/ui (Base UI engine) foundation + design tokens

> Spec for [issue #41 — Foundation: adopt shadcn/ui (Base UI engine) + design tokens, re-skin shared components](https://github.com/evanmei87/meal-planner/issues/41).
> Date: 2026-06-26 · Status: approved design, ready for implementation plan
> Decision rationale: [`docs/ui-component-research.md`](../../ui-component-research.md) (issue #10 / PR #40).

## 1. Goal

Establish the UI component-library **foundation** for the frontend: initialize shadcn/ui on the Base UI engine, define a documented set of design tokens (color, spacing, typography), and re-skin the four existing shared components onto the token system **without changing their public props/API**. Foundation-only — no new feature screens.

This lands before the exercise suite (#28–#38) so every new screen is built on the design system from day one. It unblocks the library-adoption aspect of #6, #28, #36, #37, and #38.

## 2. Decisions (locked during brainstorming)

| Decision | Choice | Consequence |
|---|---|---|
| Visual direction | **Full shadcn default aesthetic** (neutral base, near-neutral primary) | The green brand accent largely retires. Page-level green/blue buttons and the green active NavLink live *outside* the four components and are out of scope here, so some green/blue lingers until those screens are migrated by their own issues. This interim mixed look is expected. |
| Import convention | **Add `@/` alias AND migrate all existing relative imports** | One consistent convention app-wide. Broad but mechanical diff; `tsc` + tests are the safety net. |
| Button proof depth | **Generate + render test only** | `button` is added via the CLI and proven by a test; it is *not* wired into any feature page. Stays strictly inside the issue scope. |
| Re-skin approach | **Approach A — re-tokenize in place** | Keep each component's existing JSX; swap hard-coded color classes for token classes. Smallest diff, exactly-preserved API. |

## 3. Scope

**In scope**
- `npx shadcn init` against the **Tailwind-3-compatible** path (CSS-variables mode), Base UI engine; commit `components.json`, `@/lib/utils.ts` (`cn()`), and Tailwind/CSS-variable wiring.
- `@/` path alias in `tsconfig.json` + `vite.config.ts`, and migration of all existing relative cross-module imports under `web/src` to `@/`.
- Design tokens as CSS variables + Tailwind theme extension, documented in `docs/design-tokens.md`, including the exercise-type palette reused by #38.
- Re-skin `Card`, `Table`, `ErrorBanner`, `Spinner` onto the tokens; public props unchanged.
- Add one shadcn primitive (`button`) via the CLI under `web/src/components/ui/`.
- Tests: render/variant test for `Button`; render tests locking the four components' public APIs.

**Out of scope**
- Feature-specific components (#6 meal Dialog, #38 `cva` color variants, #36 drag-and-drop, calendar layout #28/#37).
- `@dnd-kit`, Tremor, MagicUI (their own issues).
- Any backend change.
- Editing feature pages (`App.tsx`, `PlanPage`, `StatePage`, etc.) to consume the new tokens — beyond the mechanical `@/` import migration. Their hard-coded green/blue states stay until their own issues migrate them.
- A dark-mode toggle (the `.dark` token block is scaffolded but dormant — no toggle wired).

## 4. Architecture & components

### 4.1 Init & config (Tailwind 3, Base UI engine)

- Initialize via `npx shadcn init` using the **Tailwind-3 / CSS-variables** configuration. Explicitly do **not** allow an upgrade to Tailwind 4 — the issue pins Tailwind 3.
- `components.json`: `style` (shadcn default), `baseColor: neutral`, `cssVariables: true`, Base UI engine, `@/` aliases (`components`, `ui`, `utils`, `lib`, `hooks`).
- New dependencies: `class-variance-authority`, `clsx`, `tailwind-merge`, `tailwindcss-animate`.
- The Base UI runtime package and `lucide-react` are pulled in only when a generated primitive needs them. `button` is pure `cva` and needs neither, so neither is added in this issue. The Base UI engine is still recorded in `components.json` for future `npx shadcn add`.
- Generated `@/lib/utils.ts` exports `cn()` (`clsx` + `tailwind-merge`).

### 4.2 `@/` alias + import migration

- `tsconfig.json`: add `baseUrl: "."` and `paths: { "@/*": ["./src/*"] }`.
- `vite.config.ts`: add `resolve.alias` mapping `@` → `./src` (Vitest inherits the same config, so tests resolve the alias too).
- Convert every existing relative cross-module import under `web/src` (`../…`, `./…` that crosses a module boundary) to `@/…`. Mechanical; no behavior change.

### 4.3 Design tokens (CSS variables + Tailwind theme extension)

**Color — shadcn default neutral set** in `:root` (and a dormant `.dark` block): `--background`, `--foreground`, `--card(-foreground)`, `--popover(-foreground)`, `--primary(-foreground)` (near-neutral), `--secondary(-foreground)`, `--muted(-foreground)`, `--accent(-foreground)`, `--destructive(-foreground)`, `--border`, `--input`, `--ring`, `--chart-1..5`.

**Color — additive exercise palette** (new CSS vars + Tailwind colors), defined and documented here; the `cva` variants that consume them belong to #38. Each type gets a strong value (border) and a subtle tint (background), mapping #38's known palette:

| Token | Source (Tailwind ref) | Used by #38 as |
|---|---|---|
| `exercise.running` / `running-subtle` | green-600 / green-50 | `border-…` / `bg-…` |
| `exercise.walking` / `walking-subtle` | blue-500 / blue-50 | `border-…` / `bg-…` |
| `exercise.biking` / `biking-subtle` | orange-500 / orange-50 | `border-…` / `bg-…` |
| `exercise.swimming` / `swimming-subtle` | cyan-500 / cyan-50 | `border-…` / `bg-…` |
| `exercise.strength` / `strength-subtle` | purple-500 / purple-50 | `border-…` / `bg-…` |

**Active/selected state:** documented to map to `bg-primary text-primary-foreground`. #28's today-highlight and #38's selected states consume this later; `App.tsx`/`PlanPage` are **not** edited in this issue.

**Spacing/shape:** adopt Tailwind's spacing scale as-is (no redundant CSS vars) + shadcn's `--radius` with derived `lg`/`md`/`sm`.

**Typography:** `--font-sans` stack wired into `fontFamily.sans`; the Tailwind type scale documented.

**Documentation deliverable:** `docs/design-tokens.md` lists every token, its value, and intended use — including the exercise palette and the active-state guidance — so downstream issues consume tokens rather than re-deriving colors.

### 4.4 Re-skin the four components (Approach A — re-tokenize in place)

Keep existing JSX and props; swap hard-coded colors for token classes.

| Component | Public API (unchanged) | Token mapping |
|---|---|---|
| `Card` | `{ children, className? }` | `bg-white` → `bg-card text-card-foreground`; `border-gray-200` → `border-border` (keep `rounded-lg shadow-sm p-4`) |
| `Table` | `{ columns, rows }` (`Column = { key, header, render? }`) | header `bg-gray-100` → `bg-muted`, `text-gray-700` → `text-muted-foreground`; rows `text-gray-700` → `text-foreground`; `border-gray-200` → `border-border`; `hover:bg-gray-50` → `hover:bg-muted/50`; empty `text-gray-400` → `text-muted-foreground` |
| `ErrorBanner` | `{ message }` | `bg-red-50 border-red-200 text-red-700` → shadcn soft-destructive idiom: `border-destructive/50 bg-destructive/10 text-destructive` |
| `Spinner` | none | `border-green-600` → `border-primary` |

### 4.5 Button primitive (workflow proof)

- `npx shadcn add button` → `web/src/components/ui/button.tsx` (cva variants: `default`/`secondary`/`destructive`/`outline`/`ghost`/`link`, sizes).
- Not consumed by any feature page in this issue.

## 5. Testing & verification

- **Button:** render/variant test — renders children, applies a variant class, exposes `role="button"`. Proves the primitive, `cva`, `@/` resolution, and Base UI engine config compile and render.
- **Four components:** small render tests asserting each renders its props' content (they currently have no tests) — locks the public API we promise not to break.
- **Regression:** existing feature-page tests stay green. They assert on text and ARIA roles, not class names, so re-skinning is safe.
- **Gates (issue acceptance criteria):** `npm test -- --run` passes and `npx tsc --noEmit` is clean, both from `web/`.

## 6. Risks & assumptions

- **Tailwind 3, not 4.** Must use shadcn's Tailwind-3 / CSS-variables init path; do not let the CLI upgrade to Tailwind 4. Pin/verify during implementation.
- **Base UI engine selection.** Verify the exact flag/prompt in the current shadcn CLI during implementation. `button` needs no Base UI runtime dep; the engine is configured for future adds.
- **Import migration breadth.** Large but mechanical; `tsc --noEmit` + the test suite are the safety net.
- **Interim mixed look.** Page-level green/blue and the green active NavLink remain hard-coded until their own issues migrate them to tokens. Expected, not a regression.
- **Dark mode dormant.** The `.dark` token block is scaffolded but no toggle is wired — out of scope.

## 7. Acceptance criteria (from the issue)

- [ ] shadcn/ui initialized against the Base UI engine; config committed (`components.json`, Tailwind/CSS-variable wiring, `@/lib/utils.ts`).
- [ ] Documented design tokens (color, spacing, typography) as CSS variables / Tailwind theme extensions, including the exercise-type palette reused by #38.
- [ ] `Card`, `Table`, `ErrorBanner`, `Spinner` re-skinned onto the tokens with unchanged public props/API.
- [ ] At least one shadcn primitive (`button`) added via the CLI under `web/src/components/ui/`.
- [ ] `npm test -- --run` and `npx tsc --noEmit` pass from `web/`.
- [ ] No regressions on the existing four tabs (Plan, Meals, Groceries, State).
