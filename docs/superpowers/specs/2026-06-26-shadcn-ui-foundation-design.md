# Design: shadcn/ui (Base UI engine) foundation + design tokens, on Tailwind 4

> Spec for [issue #41 — Foundation: adopt shadcn/ui (Base UI engine) + design tokens, re-skin shared components](https://github.com/evanmei87/meal-planner/issues/41).
> Date: 2026-06-26 · Status: approved design, ready for implementation plan
> Decision rationale: [`docs/ui-component-research.md`](../../ui-component-research.md) (issue #10 / PR #40).

## 1. Goal

Establish the UI component-library **foundation** for the frontend: **upgrade Tailwind 3 → 4**, initialize shadcn/ui on the Base UI engine (its native Tailwind 4 path), define a documented set of design tokens (color, spacing, typography), and re-skin the four existing shared components onto the token system **without changing their public props/API**. Foundation-only — no new feature screens.

This lands before the exercise suite (#28–#38) so every new screen is built on the design system from day one. It unblocks the library-adoption aspect of #6, #28, #36, #37, and #38.

## 2. Decisions (locked during brainstorming)

| Decision | Choice | Consequence |
|---|---|---|
| Tailwind version | **Upgrade to Tailwind 4 as part of this foundation** | shadcn's current default/forward path is v4. Because #41 rewrites the token plumbing anyway, doing it the v4 way avoids writing the foundation twice. Expands the regression surface to the whole app (all utility classes), handled by the official codemod + the test suite + a visual smoke pass. |
| Visual direction | **Full shadcn default aesthetic** (neutral base, near-neutral primary) | The green brand accent largely retires. Page-level green/blue buttons and the green active NavLink live *outside* the four components and are out of scope here, so some green/blue lingers until those screens are migrated by their own issues. This interim mixed look is expected. |
| Import convention | **Add `@/` alias AND migrate all existing relative imports** | One consistent convention app-wide. Broad but mechanical diff; `tsc` + tests are the safety net. |
| Button proof depth | **Generate + render test only** | `button` is added via the CLI and proven by a test; it is *not* wired into any feature page. Stays strictly inside the issue scope. |
| Re-skin approach | **Approach A — re-tokenize in place** | Keep each component's existing JSX; swap hard-coded color classes for token classes. Smallest diff, exactly-preserved API. |

## 3. Scope

**In scope**
- **Tailwind 3 → 4 upgrade** of the `web/` app (codemod + manual fixups), green build and tests before layering shadcn on top.
- `npx shadcn init` against the **Tailwind 4** path, Base UI engine; commit `components.json`, `@/lib/utils.ts` (`cn()`), and CSS-variable token wiring.
- `@/` path alias in `tsconfig.json` + `vite.config.ts`, and migration of all existing relative cross-module imports under `web/src` to `@/`.
- Design tokens as CSS variables + Tailwind `@theme` mappings, documented in `docs/design-tokens.md`, including the exercise-type palette reused by #38.
- Re-skin `Card`, `Table`, `ErrorBanner`, `Spinner` onto the tokens; public props unchanged.
- Add one shadcn primitive (`button`) via the CLI under `web/src/components/ui/`.
- Tests: render/variant test for `Button`; render tests locking the four components' public APIs.
- **Stale Tailwind-3 reference cleanup** (see §5).

**Out of scope**
- Feature-specific components (#6 meal Dialog, #38 `cva` color variants, #36 drag-and-drop, calendar layout #28/#37).
- `@dnd-kit`, Tremor, MagicUI (their own issues).
- Any backend change.
- Editing feature pages (`App.tsx`, `PlanPage`, `StatePage`, etc.) to consume the new tokens — beyond the mechanical `@/` import migration and any utility renames the Tailwind 4 codemod applies. Their hard-coded green/blue states stay until their own issues migrate them.
- A dark-mode toggle (the `.dark` token block is scaffolded but dormant — no toggle wired).
- Rewriting historical completed-work records in `plan/issue-0-web-frontend/*` (they accurately describe the original v3 scaffold — see §5).

## 4. Architecture & components

### 4.1 Tailwind 4 upgrade + shadcn init (Base UI engine)

**Upgrade sequence (verify each before the next):**

1. **Upgrade Tailwind 3 → 4.** Run `npx @tailwindcss/upgrade`, then finish the config by hand:
   - Adopt the **`@tailwindcss/vite`** plugin in `vite.config.ts`; remove the now-redundant `postcss.config.cjs` and `autoprefixer` (Tailwind 4 / Lightning CSS handles vendor prefixing).
   - `web/src/index.css`: `@tailwind base/components/utilities` → `@import "tailwindcss";`.
   - Remove `web/tailwind.config.ts` (v4 is CSS-first with automatic content detection); custom theme lives in `@theme` in CSS. Update `web/tsconfig.node.json` to drop the `tailwind.config.ts` include.
   - `web/package.json`: `tailwindcss@^4`, add `@tailwindcss/vite`; drop `tailwindcss@^3`, `autoprefixer`, and the direct `postcss` config dep.
   - **Fix v4 breaking changes that touch this app:** shadow-scale rename (v3 `shadow-sm` → v4 `shadow-xs`, used by `Card` and the nav) and ring defaults (StatePage's `ring-2 ring-green-500` is explicit, low impact). Verify the existing four tabs render unchanged and the suite is green on v4 **before** touching shadcn.
2. **`npx shadcn init`** on the Tailwind 4 path: `baseColor: neutral`, `cssVariables: true`, Base UI engine, `@/` aliases (`components`, `ui`, `utils`, `lib`, `hooks`). Generates `@/lib/utils.ts` (`cn()` = `clsx` + `tailwind-merge`) and the v4 token wiring in `index.css`.
   - New dependencies: `class-variance-authority`, `clsx`, `tailwind-merge`, and shadcn's v4 animation import (`tw-animate-css`).
   - The Base UI runtime package and `lucide-react` are pulled in only when a generated primitive needs them. `button` is pure `cva` and needs neither, so neither is added in this issue. The Base UI engine is still recorded in `components.json` for future `npx shadcn add`.

### 4.2 `@/` alias + import migration

- `tsconfig.json`: add `baseUrl: "."` and `paths: { "@/*": ["./src/*"] }`.
- `vite.config.ts`: add `resolve.alias` mapping `@` → `./src` (Vitest inherits the same config, so tests resolve the alias too).
- Convert every existing relative cross-module import under `web/src` (`../…`, `./…` that crosses a module boundary) to `@/…`. Mechanical; no behavior change.

### 4.3 Design tokens (CSS variables + Tailwind `@theme`)

Tailwind 4 + shadcn express tokens as CSS variables in `:root`/`.dark` (OKLCH values) mapped into Tailwind utilities via `@theme inline { --color-…: var(--…) }`.

**Color — shadcn default neutral set:** `--background`, `--foreground`, `--card(-foreground)`, `--popover(-foreground)`, `--primary(-foreground)` (near-neutral), `--secondary(-foreground)`, `--muted(-foreground)`, `--accent(-foreground)`, `--destructive(-foreground)`, `--border`, `--input`, `--ring`, `--chart-1..5`, plus a dormant `.dark` block.

**Color — additive exercise palette** (new CSS vars + `@theme` colors), defined and documented here; the `cva` variants that consume them belong to #38. Each type gets a strong value (border) and a subtle tint (background), in OKLCH, mapping #38's known palette:

| Token | Source (Tailwind ref) | Used by #38 as |
|---|---|---|
| `exercise-running` / `running-subtle` | green-600 / green-50 | `border-…` / `bg-…` |
| `exercise-walking` / `walking-subtle` | blue-500 / blue-50 | `border-…` / `bg-…` |
| `exercise-biking` / `biking-subtle` | orange-500 / orange-50 | `border-…` / `bg-…` |
| `exercise-swimming` / `swimming-subtle` | cyan-500 / cyan-50 | `border-…` / `bg-…` |
| `exercise-strength` / `strength-subtle` | purple-500 / purple-50 | `border-…` / `bg-…` |

**Active/selected state:** documented to map to `bg-primary text-primary-foreground`. #28's today-highlight and #38's selected states consume this later; `App.tsx`/`PlanPage` are **not** edited in this issue.

**Spacing/shape:** adopt Tailwind's spacing scale as-is (no redundant CSS vars) + shadcn's `--radius` with derived `lg`/`md`/`sm`.

**Typography:** `--font-sans` stack wired via `@theme`; the Tailwind type scale documented.

**Documentation deliverable:** `docs/design-tokens.md` lists every token, its value, and intended use — including the exercise palette and the active-state guidance — so downstream issues consume tokens rather than re-deriving colors.

### 4.4 Re-skin the four components (Approach A — re-tokenize in place)

Keep existing JSX and props; swap hard-coded colors for token classes.

| Component | Public API (unchanged) | Token mapping |
|---|---|---|
| `Card` | `{ children, className? }` | `bg-white` → `bg-card text-card-foreground`; `border-gray-200` → `border-border` (keep radius + shadow, codemod-renamed) |
| `Table` | `{ columns, rows }` (`Column = { key, header, render? }`) | header `bg-gray-100` → `bg-muted`, `text-gray-700` → `text-muted-foreground`; rows `text-gray-700` → `text-foreground`; `border-gray-200` → `border-border`; `hover:bg-gray-50` → `hover:bg-muted/50`; empty `text-gray-400` → `text-muted-foreground` |
| `ErrorBanner` | `{ message }` | `bg-red-50 border-red-200 text-red-700` → shadcn soft-destructive idiom: `border-destructive/50 bg-destructive/10 text-destructive` |
| `Spinner` | none | `border-green-600` → `border-primary` |

### 4.5 Button primitive (workflow proof)

- `npx shadcn add button` → `web/src/components/ui/button.tsx` (cva variants: `default`/`secondary`/`destructive`/`outline`/`ghost`/`link`, sizes).
- Not consumed by any feature page in this issue.

## 5. Stale Tailwind-3 reference cleanup

| Location | Action |
|---|---|
| `web/package.json`, `web/src/index.css`, `web/tailwind.config.ts`, `web/postcss.config.cjs`, `web/tsconfig.node.json` | The live upgrade (§4.1) — config rewritten/removed. |
| `docs/ui-component-research.md` (L16, L36 — "Tailwind CSS 3" / "Tailwind 3") | Update the stack description to Tailwind 4. The shadcn recommendation itself is unaffected. |
| This spec | Updated to Tailwind 4 (this revision). |
| GitHub issue #41 body | Updated: Context says Tailwind 4; an acceptance criterion for the 3→4 upgrade added. |
| `CLAUDE.md` | No version-pinned Tailwind reference (only generic "Tailwind classes") — no change. |
| `plan/issue-0-web-frontend/plan.md` + `design.md` | **Leave as-is.** Historical record of the original v3 scaffold; rewriting would falsify completed-work history. |

## 6. Testing & verification

- **Tailwind 4 upgrade:** existing four tabs render unchanged and `npm test -- --run` + `npx tsc --noEmit` are green on v4 **before** shadcn is layered on.
- **Button:** render/variant test — renders children, applies a variant class, exposes `role="button"`. Proves the primitive, `cva`, `@/` resolution, and Base UI engine config compile and render.
- **Four components:** small render tests asserting each renders its props' content (they currently have no tests) — locks the public API we promise not to break.
- **Regression:** existing feature-page tests stay green. They assert on text and ARIA roles, not class names, so the upgrade + re-skin are safe.
- **Gates (issue acceptance criteria):** `npm test -- --run` passes and `npx tsc --noEmit` is clean, both from `web/`. A manual visual smoke pass of the four tabs after the v4 upgrade.

## 7. Risks & assumptions

- **Tailwind 4 expands the regression surface** to every utility class in the app, not just the four components. Mitigated by the official codemod, the text/role-based test suite, and a visual smoke pass. This is the deliberate cost of not upgrading twice.
- **Browser-support floor rises** to Safari 16.4+ / Chrome 111+ / Firefox 128+ (Tailwind 4 uses native cascade layers, `@property`, `color-mix()`). Accepted for a personal app.
- **Base UI engine selection.** Verify the exact flag/prompt in the current shadcn CLI during implementation. `button` needs no Base UI runtime dep; the engine is configured for future adds.
- **Import migration breadth.** Large but mechanical; `tsc --noEmit` + the test suite are the safety net.
- **Interim mixed look.** Page-level green/blue and the green active NavLink remain hard-coded until their own issues migrate them to tokens. Expected, not a regression.
- **Dark mode dormant.** The `.dark` token block is scaffolded but no toggle is wired — out of scope.

## 8. Acceptance criteria

- [ ] Tailwind upgraded 3 → 4 (codemod + manual fixups: `@tailwindcss/vite` plugin, `@import` in CSS, config removed); build and tests green on v4.
- [ ] shadcn/ui initialized against the Base UI engine on Tailwind 4; config committed (`components.json`, CSS-variable token wiring, `@/lib/utils.ts`).
- [ ] Documented design tokens (color, spacing, typography) as CSS variables / `@theme` mappings, including the exercise-type palette reused by #38.
- [ ] `Card`, `Table`, `ErrorBanner`, `Spinner` re-skinned onto the tokens with unchanged public props/API.
- [ ] At least one shadcn primitive (`button`) added via the CLI under `web/src/components/ui/`.
- [ ] Stale Tailwind-3 references cleaned up per §5.
- [ ] `npm test -- --run` and `npx tsc --noEmit` pass from `web/`.
- [ ] No regressions on the existing four tabs (Plan, Meals, Groceries, State).
