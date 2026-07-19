# Design System North Star & Self-Validation Loop

**Date:** 2026-07-19
**Status:** Approved design, pending implementation plan
**GitHub issue:** none (use `0` for the implementation plan directory)

## Problem

The repository contains two divergent design systems.

The first is intentional: eleven primitives in `web/src/components` (`Button`, `Card`, `Dialog`, `Table`, `Spinner`, `ErrorBanner`, and the `Dialog*` family), built on `@base-ui/react`, styled with `cva`, themed through semantic CSS custom properties in `web/src/index.css`. Every one has been graded through `.design-sync` and carries verdict `"good"`.

The second is accidental: the four feature pages, written in raw Tailwind that largely bypasses the first.

Measured on the current tree (`web/src/features/**`, tests excluded):

| Signal | Count |
|---|---|
| Raw palette utilities (`bg-green-600`, `text-gray-500`, `border-gray-300`, …) | 69 |
| Hand-rolled `<button>` elements | 9 |
| `<input>` / `<select>` / `<textarea>` tags, **all** carrying ad-hoc border classes | 11 |
| Imports of `Button` in feature pages | 0 |

`Card`, `Table`, `Spinner`, and `ErrorBanner` were adopted. `Button` never was — each page reimplements `px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-sm font-medium` inline. An identical input class string is duplicated verbatim across all four pages.

`bg-green-600` is a Tailwind palette literal, not a token. It does not resolve through `--color-primary`. Theme changes will not reach these pages.

### Why this stayed invisible

Two causes, both structural rather than accidental:

1. **`conventions.md` documents mechanics, not intent.** It states how to hold the tools — use `cva`, compose with `cn()`, never hardcode hex values — but never states what a correct screen looks like. There was no artifact to validate a page against.
2. **The existing grading loop scores components in isolation.** Consistency is a relational property between screens. A per-component preview cannot express it. The loop reported eleven `"good"` verdicts while the pages consuming those components drifted freely.

Note that the naive audit — grepping for hex literals and `style={{}}` — returns almost nothing (one legitimate dynamic width in `MacroDisplay`). It measures the wrong thing and produces false confidence. Any checker built here must target palette utilities and un-adopted primitives, which is where the drift actually lives.

## Goals

- State a north star: what "correct" means for this UI, in a form both a human and a script can read.
- Give the development loop an automatic mechanical gate that cannot be forgotten.
- Give it a deliberate visual review that catches drift no rule can express.
- Freeze existing debt without blocking work, and drain it as files are touched.

## Non-goals

- Migrating the 89 existing violations. The ratchet absorbs these incrementally.
- Revising the primitives. They are graded and passing; the standard is not the problem.
- Extending the gate to `web/src/components/**`. Initial scope is `web/src/features/**`.

## Design

### 1. North star document

New file `.design-sync/north-star.md`, alongside `conventions.md` rather than replacing it. `conventions.md` remains the *how*. The north star is the *what*, and is the single place rules are written down.

**Intent section** — one paragraph stating the goal a rule cannot capture: four pages that read as one application, authored by one person. This is the standard Tier 2 grades against.

**Invariants section** — a numbered table, each row tagged with its enforcement tier:

| # | Invariant | Tier |
|---|---|---|
| 1 | Color only via semantic tokens; no palette literals | 1 (machine) |
| 2 | Every interactive control is `Button`; no bare `<button>` | 1 (machine) |
| 3 | Text entry uses a shared `Input` primitive | 1 (machine) — blocked, see Known gaps |
| 4 | Sections are `Card`; page roots share one vertical rhythm | 2 (judged) |
| 5 | Typography uses the fixed scale (page title / section heading / body / muted) | 2 (judged) |
| 6 | Density and alignment match across pages | 2 (judged) |

**Each rule declares its own tier, in this table.** The Tier 1 checker derives its rule list from these entries. One source of truth, so the document and the linter cannot quietly disagree as the system evolves.

**Known gaps section** — records invariants that are stated but not yet satisfiable, so the distinction between "not enforced" and "cannot be enforced" stays explicit.

### 2. Tier 1 — mechanical gate

`.design-sync/check/ds-check.mjs`. Plain Node, no new dependencies. Scope `web/src/features/**`, excluding `*.test.tsx`.

Rules:

| Rule | Detection |
|---|---|
| `no-raw-palette` | `(bg\|text\|border\|ring\|from\|to\|via)-(gray\|green\|blue\|amber\|red\|slate\|zinc)-\d{2,3}` |
| `no-bare-button` | `<button` outside `web/src/components/` |
| `no-adhoc-input` | brace-aware tag scan for `<input` / `<select` / `<textarea` whose open-tag contains a `border-` class |
| `no-inline-style` | `style={{`, allowlisting genuinely dynamic values |

The `no-inline-style` allowlist covers `MacroDisplay.tsx`'s percentage width, which is a legitimate runtime value and stays.

#### Detection constraint: JSX tags need a brace-aware scanner

Two naive approaches were tried and both produced confidently wrong numbers:

1. **`<(input|select|textarea)[^>]*border-` matches nothing.** JSX props contain arrow functions, and the `>` in `=>` terminates the character class before it reaches `className`. Reports 0 of 11.
2. **Line-based (tag and `border-` on the same line) reports 7 of 11.** Most inputs here are multi-line JSX, so the `className` sits several lines below the tag opener.

Detection therefore uses a small brace-aware tag scanner: locate `<input` / `<select` / `<textarea`, then scan forward tracking `{}` depth and end the tag at the first `>` found at depth 0. This survives both arrow functions and newlines, and is validated at 11 of 11 on the current tree. It is roughly twenty lines and needs no parser.

AST-based detection was rejected: `ts-morph` exists only in `.ds-sync/node_modules`, and `.ds-sync/` is gitignored (`.gitignore:45`), so depending on it would break on a fresh clone. `typescript` is present in `web/devDependencies` if a future version needs real parsing.

**This is the central lesson of the audit, now encoded as a requirement:** every wrong number above was produced by a check that ran successfully and returned a plausible answer. Silence is not evidence of cleanliness. Each rule ships with a fixture test pinning its expected count.

#### Baseline ratchet

`.design-sync/check/baseline.json`, checked into git:

```json
{
  "no-raw-palette": 69,
  "no-bare-button": 9,
  "no-adhoc-input": 11,
  "no-inline-style": 0
}
```

The gate fails only when a count **exceeds** its baseline.

- **Ratchets down automatically.** When a count drops, the script rewrites the baseline lower and reports it. Removed debt cannot silently return.
- **Never ratchets up.** Raising a baseline requires hand-editing the file — a visible, reviewable diff. The script cannot relax its own constraint to turn a failure green.

Failure output names `file:line` for **new violations only**. A gate that prints 89 pre-existing problems on every failure trains the reader to ignore it.

### 3. Tier 2 — visual review

A `/ds-review` skill at `.claude/skills/ds-review/SKILL.md`, invoked deliberately. Playwright capture is too slow to attach to a per-turn hook.

Flow: the existing `run-app` skill brings up both servers; browser tools drive the four feature pages at desktop (1280×800) and mobile (375×812); screenshots are graded against Tier 2 invariants.

Output goes to `.design-sync/.cache/review/<Page>.grade.json`, reusing the existing grade shape so page and component grades share one format. Note that `.design-sync/.cache/` is gitignored (`.gitignore:47`), so these grades are local and ephemeral — consistent with how component grades already work, but it means Tier 2 findings do not travel into commits or PRs. Tier 1 is the only tier with a durable, checked-in artifact.

```json
{
  "cells": {
    "Desktop": { "verdict": "good" },
    "Mobile": {
      "verdict": "drift",
      "notes": ["Section heading is text-lg here, text-2xl on MealDetailPage"]
    }
  }
}
```

**The rubric compares pages against each other, not against an abstract ideal.** "Does this page look good?" is barely answerable and invites a worthless affirmative. "Is the section-heading size identical across all four pages?" is answerable from four screenshots side by side and yields a specific fix. This directly addresses the root cause in the Problem section: isolation is the condition under which drift is invisible, so the review must be relational.

Rubric dimensions: heading scale, card padding, control height, page vertical rhythm, empty-state treatment, loading-state treatment. Each produces a named discrepancy or passes.

### 4. Wiring

**Stop hook** in `.claude/settings.json`, added via the `update-config` skill:

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [{ "type": "command", "command": "node .design-sync/check/ds-check.mjs --gate" }] }
    ]
  }
}
```

Silent on pass; non-zero exit with new violations on failure. Regex over roughly ten files, so single-digit milliseconds — cheap enough to fire every turn unnoticed.

A `Stop` hook was chosen over an npm script or a manually invoked skill because both alternatives route enforcement through the assistant remembering to run them, which is the unreliable component this design exists to work around.

**`CLAUDE.md`** gains a pointer to `north-star.md`, placing the standard in context during authoring. The hook is a backstop, not the primary channel — code should be correct before the gate runs, not corrected because it failed.

## Verification

Each criterion is pass/fail, not "it runs":

1. `ds-check` on the current tree reports **69 / 9 / 11 / 0**, matching independently verified counts — confirms the checker measures accurately rather than merely executing.
   A `no-adhoc-input` result of 0 indicates the `[^>]*` bug and 7 indicates line-based scanning; only 11 is correct.
   `no-inline-style` is 0 *after* allowlisting; the raw occurrence count is 1 (`MacroDisplay.tsx:40`). If it reports 1, the allowlist is not wired.
2. Introducing a deliberate `bg-green-600` fails the gate, naming that `file:line` and only that one.
3. Converting one hand-rolled button to `Button` ratchets `no-bare-button` to 8 automatically.
4. Hand-editing a baseline upward produces a visible diff and is not something the script performs.
5. A real Stop event fires the hook — verified directly, because an unwired hook is silent and therefore indistinguishable from a passing one.

## Known gaps and risks

- **Invariant 3 is unenforceable on arrival.** No `Input` primitive exists. The identical four-page input class string is a component that was never extracted. `ds-check` will report `no-adhoc-input` counts, but there is no sanctioned replacement to migrate toward. Extracting `Input` is follow-up work.
- **Tier 2 depends on judgment.** Comparison-framed questions constrain it substantially, but it will not be perfectly repeatable across runs.
- **Regex detection has known limits.** Class names assembled at runtime through template literals still evade `no-raw-palette`; `PlanPage.tsx:83` already builds classes this way. Accepted: the rule catches the common case and Tier 2 is the backstop. (Multi-line JSX is *not* a gap — the brace-aware scanner handles it.)
- **The checker needs its own test.** A rule that matches nothing is indistinguishable from a clean codebase. Three separate counting attempts during this design returned 0, 7, and 62 — every one of them ran without error. Each rule ships with a fixture test pinning expected counts, so a rule that silently stops matching fails loudly instead of passing.
- **Scope is `features/` only.** Primitives may contain their own palette literals; that is out of scope here and worth a separate audit.
