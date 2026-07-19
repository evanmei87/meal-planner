# Meal Planner UI — North Star

`conventions.md` describes *how* to use the tools. This file describes *what correct looks like*, and is the single source for every design invariant. Rules are not written down anywhere else.

## Intent

Four feature pages that read as one application, authored by one person.

A reader moving from Plan to Meals to Groceries to State should notice no seam: headings are the same size, cards have the same padding, controls have the same height, and the vertical rhythm does not change. Individual pages looking acceptable in isolation is not the goal and is not sufficient — consistency is a property *between* screens, which is why Tier 2 grades them against each other rather than one at a time.

## Invariants

Each invariant declares its enforcement tier. Tier 1 rows are machine-checked by `.design-sync/check/ds-check.mjs`; the rule ID is the key in `baseline.json`. Tier 2 rows are judged by `/ds-review`.

| # | Invariant | Tier | Rule ID |
|---|---|---|---|
| 1 | Color comes only from semantic tokens. No Tailwind palette literals (`bg-green-600`, `text-gray-500`). | 1 | `no-raw-palette` |
| 2 | Every interactive control is `Button`. No bare `<button>`. | 1 | `no-bare-button` |
| 3 | Text entry uses a shared `Input` primitive. No ad-hoc bordered inputs. | 1 | `no-adhoc-input` |
| 4 | No inline `style` for themeable values. | 1 | `no-inline-style` |
| 5 | Sections are `Card`; page roots share one vertical rhythm. | 2 | — |
| 6 | Typography uses the fixed scale: page title / section heading / body / muted. | 2 | — |
| 7 | Density and alignment match across pages. | 2 | — |

## Known gaps

- **Invariant 3 has no primitive to migrate toward.** No `Input` component exists. All 11 input tags in `features/` hand-roll `border border-gray-300 rounded px-3 py-2 text-sm`, and the same class string is duplicated across four pages. `no-adhoc-input` counts these, but nothing can be fixed until `Input` is extracted. Follow-up work.
- **Runtime-composed class names evade Tier 1.** `PlanPage.tsx:83` builds classes in a template literal; the regex cannot see inside. Tier 2 is the backstop.
- **Scope is `features/` only.** The primitives in `web/src/components/` have not been audited against invariant 1.

## Adding an invariant

Add a row to the table with a tier. If Tier 1, add a rule to `ds-check.mjs`, a fixture test, and a `baseline.json` entry. If Tier 2, add a rubric line to the `/ds-review` skill. The table is the source; enforcement follows it.
