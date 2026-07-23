# Issue #43 — Optional: UI animation polish via MagicUI

GitHub issue: https://github.com/evanmei87/meal-planner/issues/43

## Context

Marked optional/low-priority in the original UI component research
(`docs/ui-component-research.md` §6), gated on the exercise suite (#28–#38)
and nutrition charts (#42) shipping first. Both have now shipped, so this
picks the option back up.

## Scope

Both effects the issue asks for — a looping pulse ring and a one-shot
fade+slide reveal — are CSS keyframe loops/transitions with no need for a JS
animation runtime. The project already ships everything required:
`tw-animate-css` (already a dependency, already imported in
`web/src/index.css`) provides `animate-in`/`fade-in`/`slide-in-from-*`
utilities, and Tailwind core ships `animate-ping`/`animate-pulse` plus a
built-in `motion-reduce:` variant for `prefers-reduced-motion` — all pure
CSS, no `useReducedMotion()` hook or extra dependency needed. An earlier
version of this plan added `framer-motion` for these two effects; that was
reworked after review flagged it against the issue's own acceptance
criterion of no measurable bundle-size regression (framer-motion added
+41.13kB gzip for effects CSS already covers). Add two small, on-demand
components under `web/src/components/magicui/` — no bulk import of a
MagicUI kit, no core component or data-viz changes (both explicitly out of
scope per the issue).

Target surfaces (2, reusing 2 components across 3 wire-ups — the issue's own
suggested examples):

1. **Plan-generation feedback** (`PlanPage.tsx`) — the Generate button gets a
   soft pulsing ring while a generation request is in flight, replacing the
   plain "Generating…" text-only state with a small in-progress cue.
2. **Day/tab content transitions** — switching the selected day on the Plan
   page and on the Exercise calendar page now fades + slides the day's
   content in, instead of swapping instantly.

Components:

- `BlurFade` — fade/slide-in reveal wrapper, keyed by the current tab/day id
  so changing the key re-triggers the reveal.
- `PulsatingButton` — wraps a button with an animated pulsing ring while an
  action is pending.

Both use Tailwind's `motion-reduce:` variant to freeze the animation via CSS
when the user has `prefers-reduced-motion` set — no JS media-query check.

## Verification

- `npm test -- --run` — all tests pass, including new tests for the two
  components (render children; still render when reduced motion is
  requested).
- `npx tsc --noEmit` — no errors.
- `npm run build` — bundle size compared gzip'd JS before/after to confirm
  no measurable regression, since both effects are pure CSS.
- `node .design-sync/check/ds-check.mjs --gate` from repo root — no new
  Tier 1 violations (the new components live outside the checked
  `web/src/features/` scope; the two edited feature files only add
  non-native wrapper elements, no raw palette/bare-button/ad-hoc-input/inline
  style).
