---
name: ds-review
description: Use when reviewing the meal-planner UI for design system drift, before a PR that changes page layout, or when asked to check whether pages look consistent.
---

# Design Review — Tier 2 Visual Check

Grades the four feature pages against each other for the Tier 2 invariants in `.design-sync/north-star.md`. Tier 1 is already enforced by the Stop hook; do not re-check it here.

## Why pages are compared, not scored individually

Consistency is a property *between* screens. "Does this page look good?" invites a useless yes. Every question below compares pages, so the answer is either a named discrepancy or a pass. The existing component grading loop missed all current drift precisely because it looked at components one at a time.

## Steps

1. Start the app using the `run-app` skill (both servers must be up).
2. For each page, at desktop (1280×800) and mobile (375×812), take a screenshot:
   - `/` — PlanPage
   - `/meals` — MealsPage
   - `/groceries` — GroceriesPage
   - `/state` — StatePage
3. Work through the rubric with all four screenshots in view at once.
4. Write one grade file per page.

## Rubric

Answer each across all four pages together. Record a discrepancy only when you can name both sides of it.

| Dimension | Question |
|---|---|
| Heading scale | Is the section-heading size identical on every page? |
| Page title | Does every page treat its title the same way, or do some lack one? |
| Card padding | Is padding inside bordered sections the same everywhere? |
| Control height | Do buttons and inputs share one height across pages? |
| Vertical rhythm | Is the gap between top-level sections the same on every page? |
| Empty state | Do "no items" states look like they were designed together? |
| Loading state | Does every page use the same spinner treatment and placement? |
| Mobile reflow | Does any page break or overflow at 375px while others adapt? |

## Output

Write `.design-sync/.cache/review/<Page>.grade.json`, reusing the shape of the existing component grades:

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

Use verdict `good` when nothing differs, `drift` with a `notes` array naming both sides, or `broken` for layout that fails outright.

Note that `.design-sync/.cache/` is gitignored, so these grades are local only and do not travel into a PR. Summarize findings in chat as well.

## Record the review

After writing the grade files, stamp the reviewed state so the Stop hook stops reporting the review as overdue:

```bash
node -e "import('./.design-sync/check/lib/stamp.mjs').then(m=>{m.writeStamp(m.currentStamp());console.log('stamped',m.currentStamp())})"
```

Commit `.design-sync/check/review-stamp.json` alongside the change being reviewed. Only stamp after actually working the rubric — stamping without reviewing silences the notice permanently and is the one way to defeat this tier entirely.

## Reporting

Report only named discrepancies. "Looks consistent" is a valid result when every rubric row passes; a vague positive when rows were not actually checked is not.
