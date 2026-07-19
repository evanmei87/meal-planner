# Design System North Star & Self-Validation Loop — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**GitHub issue:** none (`issue-0`)
**Spec:** [`docs/superpowers/specs/2026-07-19-design-system-north-star-design.md`](../../docs/superpowers/specs/2026-07-19-design-system-north-star-design.md)

**Goal:** Give this repo a written design-system north star plus a two-tier self-check — an automatic mechanical gate on every turn, and a deliberate visual review — so page-level drift from the design system is caught as it happens instead of accumulating invisibly.

**Architecture:** A single markdown document (`.design-sync/north-star.md`) holds every invariant, each tagged Tier 1 (machine-checked) or Tier 2 (judged). A dependency-free Node script (`.design-sync/check/ds-check.mjs`) enforces the Tier 1 invariants against `web/src/features/**`, comparing counts to a checked-in `baseline.json` that ratchets down but never up. A `Stop` hook runs that script every turn, blocking on Tier 1 regressions.

Tier 2 cannot run in a hook — it needs both servers, a browser, and model judgment. So the hook tracks *staleness* instead: `/ds-review` stamps a hash of the `className` values it reviewed, and the hook reports when they have changed since. That notice is advisory and never blocks; `CLAUDE.md` instructs the assistant to raise it before a commit or push, or when reporting visual work complete. Hashing className only means logic refactors do not trigger it — a notice that fires constantly is a notice that gets ignored.

**Tech Stack:** Node 24 (native `node:test`, `node:fs.globSync`), plain ESM, no new dependencies. Existing: React 18 + TypeScript + Tailwind v4 + `@base-ui/react` in `web/`.

## Global Constraints

- **No new npm dependencies.** There is no root `package.json`; the checker runs as bare `node`. Do not add one.
- **Do not depend on `.ds-sync/node_modules`.** `.ds-sync/` is gitignored (`.gitignore:45`) and absent on a fresh clone.
- **Scope of all Tier 1 rules:** `web/src/features/*/*.tsx`, excluding `*.test.tsx`. Exactly 8 files today.
- **Verified baseline counts on the current tree:** `no-raw-palette` **69**, `no-bare-button` **9**, `no-adhoc-input` **11**, `no-inline-style` **0** (1 raw occurrence at `MacroDisplay.tsx:40`, allowlisted).
- **Never use `[^>]*` to span a JSX tag.** `=>` in props closes the character class. Use the brace-aware scanner from Task 2.
- **Do not migrate violations.** This plan builds the loop only. The 89 existing violations stay.
- **Commit plan files.** Per `CLAUDE.md`, everything under `plan/` is staged and committed before any PR.
- **Windows/Git Bash environment.** Use forward slashes in code; the Bash tool is POSIX sh, not PowerShell.

---

### Task 1: North star document

**Files:**
- Create: `.design-sync/north-star.md`

**Interfaces:**
- Consumes: nothing
- Produces: the invariant table that Task 3's rule IDs and Task 8's rubric must match. Rule IDs defined here: `no-raw-palette`, `no-bare-button`, `no-adhoc-input`, `no-inline-style`.

- [ ] **Step 1: Write the document**

Create `.design-sync/north-star.md`:

```markdown
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
```

- [ ] **Step 2: Verify rule IDs are self-consistent**

Run: `grep -oE 'no-[a-z-]+' .design-sync/north-star.md | sort -u`
Expected exactly:
```
no-adhoc-input
no-bare-button
no-inline-style
no-raw-palette
```

- [ ] **Step 3: Commit**

```bash
git add .design-sync/north-star.md
git commit -m "docs: add design system north star with tiered invariants"
```

---

### Task 2: Brace-aware JSX tag scanner

The scanner is its own task because every later rule depends on it and it is the single component where naive implementations silently return wrong answers.

**Files:**
- Create: `.design-sync/check/lib/scan-tags.mjs`
- Test: `.design-sync/check/lib/scan-tags.test.mjs`

**Interfaces:**
- Consumes: nothing
- Produces: `extractTags(src: string, names: string[]) => Array<{name: string, text: string, index: number}>` — `text` is the full open-tag source including `<` and `>`; `index` is the character offset of `<` in `src`. Used by Task 3's `no-adhoc-input` and `no-bare-button` rules.

- [ ] **Step 1: Write the failing test**

Create `.design-sync/check/lib/scan-tags.test.mjs`:

```javascript
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { extractTags } from './scan-tags.mjs'

test('extracts a simple self-closing tag', () => {
  const tags = extractTags('<input className="a" />', ['input'])
  assert.equal(tags.length, 1)
  assert.equal(tags[0].name, 'input')
  assert.match(tags[0].text, /className="a"/)
})

test('does not stop at the > inside an arrow function', () => {
  const src = '<input onChange={(e) => set(e)} className="border-gray-300" />'
  const tags = extractTags(src, ['input'])
  assert.equal(tags.length, 1)
  assert.match(tags[0].text, /border-gray-300/, 'className after => must be captured')
})

test('spans newlines in multi-line JSX', () => {
  const src = [
    '<input',
    '  value={v}',
    '  className="border border-gray-300"',
    '/>',
  ].join('\n')
  const tags = extractTags(src, ['input'])
  assert.equal(tags.length, 1)
  assert.match(tags[0].text, /border-gray-300/)
})

test('handles nested braces in props', () => {
  const src = '<input style={{ width: `${p}%` }} className="x" />'
  const tags = extractTags(src, ['input'])
  assert.equal(tags.length, 1)
  assert.match(tags[0].text, /className="x"/)
})

test('captures non-self-closing tags such as select', () => {
  const src = '<select className="border-gray-300"><option/></select>'
  const tags = extractTags(src, ['select'])
  assert.equal(tags.length, 1)
  assert.match(tags[0].text, /border-gray-300/)
  assert.doesNotMatch(tags[0].text, /option/, 'open tag only, not children')
})

test('matches multiple names and reports each occurrence', () => {
  const src = '<input a /><textarea b /><input c />'
  const tags = extractTags(src, ['input', 'textarea'])
  assert.deepEqual(tags.map((t) => t.name), ['input', 'textarea', 'input'])
})

test('does not match a name that is a prefix of a longer tag', () => {
  const tags = extractTags('<inputGroup x />', ['input'])
  assert.equal(tags.length, 0, 'word boundary must prevent inputGroup matching input')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test .design-sync/check/lib/scan-tags.test.mjs`
Expected: FAIL — `Cannot find module` for `scan-tags.mjs`.

- [ ] **Step 3: Write minimal implementation**

Create `.design-sync/check/lib/scan-tags.mjs`:

```javascript
/**
 * Extract JSX open-tags for the given element names.
 *
 * A regex like `<input[^>]*>` cannot be used here: JSX props contain arrow
 * functions, and the `>` in `=>` closes the character class before reaching
 * className. This scans forward tracking brace depth instead, so it survives
 * both arrow functions and newlines.
 *
 * @param {string} src source text
 * @param {string[]} names element names, e.g. ['input', 'select']
 * @returns {Array<{name: string, text: string, index: number}>} open tags
 */
export function extractTags(src, names) {
  const tags = []
  const opener = new RegExp(`<(${names.join('|')})\\b`, 'g')
  let match
  while ((match = opener.exec(src))) {
    const end = findTagEnd(src, match.index + match[0].length)
    tags.push({
      name: match[1],
      text: src.slice(match.index, end + 1),
      index: match.index,
    })
  }
  return tags
}

/** Index of the `>` closing this tag, skipping any `>` nested inside braces. */
function findTagEnd(src, start) {
  let depth = 0
  for (let i = start; i < src.length; i++) {
    const char = src[i]
    if (char === '{') depth++
    else if (char === '}') depth--
    else if (char === '>' && depth === 0) return i
  }
  return src.length - 1
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test .design-sync/check/lib/scan-tags.test.mjs`
Expected: PASS, 7 tests.

- [ ] **Step 5: Commit**

```bash
git add .design-sync/check/lib/scan-tags.mjs .design-sync/check/lib/scan-tags.test.mjs
git commit -m "feat: add brace-aware JSX tag scanner for design checks"
```

---

### Task 3: Rule definitions

**Files:**
- Create: `.design-sync/check/lib/rules.mjs`
- Test: `.design-sync/check/lib/rules.test.mjs`

**Interfaces:**
- Consumes: `extractTags` from `.design-sync/check/lib/scan-tags.mjs` (Task 2)
- Produces:
  - `RULES: Array<{id: string, describe: string, find: (src: string, file: string) => Array<{line: number, text: string}>}>`
  - `lineOf(src: string, index: number) => number` — 1-indexed line number for a character offset
  - Rule IDs, in this order: `no-raw-palette`, `no-bare-button`, `no-adhoc-input`, `no-inline-style`

- [ ] **Step 1: Write the failing test**

Create `.design-sync/check/lib/rules.test.mjs`:

```javascript
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { RULES, lineOf } from './rules.mjs'

const rule = (id) => {
  const found = RULES.find((r) => r.id === id)
  assert.ok(found, `rule ${id} must exist`)
  return found
}

test('rule ids match the north star table', () => {
  assert.deepEqual(
    RULES.map((r) => r.id),
    ['no-raw-palette', 'no-bare-button', 'no-adhoc-input', 'no-inline-style'],
  )
})

test('lineOf is 1-indexed', () => {
  assert.equal(lineOf('a\nb\nc', 0), 1)
  assert.equal(lineOf('a\nb\nc', 2), 2)
  assert.equal(lineOf('a\nb\nc', 4), 3)
})

test('no-raw-palette flags palette literals', () => {
  const hits = rule('no-raw-palette').find('<div className="bg-green-600 text-gray-500" />', 'f.tsx')
  assert.equal(hits.length, 2)
})

test('no-raw-palette ignores semantic tokens', () => {
  const hits = rule('no-raw-palette').find('<div className="bg-card text-muted-foreground" />', 'f.tsx')
  assert.equal(hits.length, 0)
})

test('no-raw-palette ignores the exercise token family', () => {
  const hits = rule('no-raw-palette').find('<div className="text-exercise-running" />', 'f.tsx')
  assert.equal(hits.length, 0, 'semantic exercise-* tokens are not palette literals')
})

test('no-bare-button flags a bare button element', () => {
  const hits = rule('no-bare-button').find('<button onClick={go}>Go</button>', 'f.tsx')
  assert.equal(hits.length, 1)
})

test('no-bare-button ignores the Button component', () => {
  const hits = rule('no-bare-button').find('<Button onClick={go}>Go</Button>', 'f.tsx')
  assert.equal(hits.length, 0, 'capital-B Button is the sanctioned primitive')
})

test('no-adhoc-input flags a bordered input across newlines and arrow functions', () => {
  const src = [
    '<input',
    '  onChange={(e) => set(e.target.value)}',
    '  className="border border-gray-300 rounded px-3"',
    '/>',
  ].join('\n')
  const hits = rule('no-adhoc-input').find(src, 'f.tsx')
  assert.equal(hits.length, 1, 'must not be defeated by => or newlines')
})

test('no-adhoc-input ignores an unstyled input', () => {
  const hits = rule('no-adhoc-input').find('<input type="checkbox" />', 'f.tsx')
  assert.equal(hits.length, 0)
})

test('no-inline-style flags an inline style prop', () => {
  const hits = rule('no-inline-style').find('<div style={{ color: "red" }} />', 'f.tsx')
  assert.equal(hits.length, 1)
})

test('no-inline-style allowlists the MacroDisplay dynamic width', () => {
  const src = '<div style={{ width: `${pct(segment.grams)}%` }} />'
  const hits = rule('no-inline-style').find(src, 'web/src/features/meals/MacroDisplay.tsx')
  assert.equal(hits.length, 0, 'dynamic width in MacroDisplay is a sanctioned exception')
})

test('no-inline-style still flags other files with the same shape', () => {
  const src = '<div style={{ width: `${x}%` }} />'
  const hits = rule('no-inline-style').find(src, 'web/src/features/plan/PlanPage.tsx')
  assert.equal(hits.length, 1, 'allowlist is per-file, not per-pattern')
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test .design-sync/check/lib/rules.test.mjs`
Expected: FAIL — `Cannot find module` for `rules.mjs`.

- [ ] **Step 3: Write minimal implementation**

Create `.design-sync/check/lib/rules.mjs`:

```javascript
import { extractTags } from './scan-tags.mjs'

/** 1-indexed line number for a character offset. */
export function lineOf(src, index) {
  let line = 1
  for (let i = 0; i < index && i < src.length; i++) {
    if (src[i] === '\n') line++
  }
  return line
}

const PALETTE_FAMILIES = ['gray', 'green', 'blue', 'amber', 'red', 'slate', 'zinc', 'orange', 'cyan', 'purple']
const PALETTE = new RegExp(
  `\\b(?:bg|text|border|ring|from|to|via)-(?:${PALETTE_FAMILIES.join('|')})-\\d{2,3}\\b`,
  'g',
)

/** Files permitted to use inline style, with the reason. */
const INLINE_STYLE_ALLOWLIST = [
  // Percentage bar width is a runtime value and cannot be a Tailwind class.
  'web/src/features/meals/MacroDisplay.tsx',
]

const matchAll = (src, regex) =>
  [...src.matchAll(regex)].map((m) => ({ line: lineOf(src, m.index), text: m[0] }))

const tagsContaining = (src, names, needle) =>
  extractTags(src, names)
    .filter((tag) => needle.test(tag.text))
    .map((tag) => ({ line: lineOf(src, tag.index), text: `<${tag.name}>` }))

export const RULES = [
  {
    id: 'no-raw-palette',
    describe: 'Tailwind palette literal; use a semantic token',
    find: (src) => matchAll(src, PALETTE),
  },
  {
    id: 'no-bare-button',
    describe: 'bare <button>; use the Button primitive',
    find: (src) => extractTags(src, ['button']).map((tag) => ({ line: lineOf(src, tag.index), text: '<button>' })),
  },
  {
    id: 'no-adhoc-input',
    describe: 'ad-hoc styled input; use a shared Input primitive',
    find: (src) => tagsContaining(src, ['input', 'select', 'textarea'], /border-/),
  },
  {
    id: 'no-inline-style',
    describe: 'inline style prop; use tokens and Tailwind classes',
    find: (src, file) => {
      const normalized = file.replace(/\\/g, '/')
      if (INLINE_STYLE_ALLOWLIST.some((allowed) => normalized.endsWith(allowed))) return []
      return matchAll(src, /style=\{\{/g)
    },
  },
]
```

Note on `no-bare-button`: `extractTags` uses `<(button)\b`, and `\b` after `button` does not match in `<Button` because the regex is case-sensitive — `<B` never matches `<button`. The test asserts this.

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test .design-sync/check/lib/rules.test.mjs`
Expected: PASS, 12 tests.

- [ ] **Step 5: Commit**

```bash
git add .design-sync/check/lib/rules.mjs .design-sync/check/lib/rules.test.mjs
git commit -m "feat: add design system rule definitions with fixture tests"
```

---

### Task 4: Checker CLI with real-tree assertion

**Files:**
- Create: `.design-sync/check/lib/files.mjs`
- Create: `.design-sync/check/ds-check.mjs`
- Test: `.design-sync/check/ds-check.test.mjs`

**Interfaces:**
- Consumes: `RULES` from `./lib/rules.mjs` (Task 3)
- Produces:
  - `scopedFiles() => string[]` from `lib/files.mjs` — in-scope source paths, repo-relative with forward slashes. **Lives in its own module so Task 6's `stamp.mjs` can use it without importing `ds-check.mjs`, which would create a cycle once `ds-check.mjs` imports `reviewIsStale` in Task 7.**
  - `collectViolations() => Record<string, Array<{file: string, line: number, text: string}>>` keyed by rule ID
  - `countsOf(violations) => Record<string, number>`
  - CLI: bare `node ds-check.mjs` prints a report; `--json` prints machine-readable counts

- [ ] **Step 1: Write the failing test**

This test pins the checker against the real repository, so a rule that silently stops matching fails loudly. Create `.design-sync/check/ds-check.test.mjs`:

```javascript
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { collectViolations, countsOf } from './ds-check.mjs'

// Verified independently against the tree on 2026-07-19. If a refactor
// legitimately changes these, update baseline.json in the same commit.
const EXPECTED = {
  'no-raw-palette': 69,
  'no-bare-button': 9,
  'no-adhoc-input': 11,
  'no-inline-style': 0,
}

test('scans exactly the 8 in-scope feature files', () => {
  const violations = collectViolations()
  const files = new Set(Object.values(violations).flat().map((v) => v.file))
  for (const file of files) {
    assert.match(file, /^web\/src\/features\/[^/]+\/[^/]+\.tsx$/)
    assert.doesNotMatch(file, /\.test\.tsx$/)
  }
})

test('reports the verified counts for the current tree', () => {
  assert.deepEqual(countsOf(collectViolations()), EXPECTED)
})

test('no rule silently matches nothing', () => {
  const counts = countsOf(collectViolations())
  // no-inline-style is legitimately 0 (its only occurrence is allowlisted).
  const mustBeNonZero = ['no-raw-palette', 'no-bare-button', 'no-adhoc-input']
  for (const id of mustBeNonZero) {
    assert.ok(counts[id] > 0, `${id} returned 0 — likely a broken pattern, not a clean tree`)
  }
})

test('violations carry a usable file and line', () => {
  const hit = collectViolations()['no-bare-button'][0]
  assert.ok(hit.file.endsWith('.tsx'))
  assert.ok(Number.isInteger(hit.line) && hit.line > 0)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test .design-sync/check/ds-check.test.mjs`
Expected: FAIL — `Cannot find module` for `ds-check.mjs`.

- [ ] **Step 3: Write minimal implementation**

First create `.design-sync/check/lib/files.mjs`:

```javascript
import { globSync } from 'node:fs'

const SCOPE = 'web/src/features/*/*.tsx'

/** In-scope source files, repo-relative with forward slashes. */
export function scopedFiles() {
  return globSync(SCOPE)
    .map((f) => f.replace(/\\/g, '/'))
    .filter((f) => !f.endsWith('.test.tsx'))
    .sort()
}
```

Then create `.design-sync/check/ds-check.mjs`:

```javascript
#!/usr/bin/env node
import { readFileSync } from 'node:fs'
import { RULES } from './lib/rules.mjs'
import { scopedFiles } from './lib/files.mjs'

export { scopedFiles }

/** All violations, keyed by rule id. */
export function collectViolations() {
  const result = Object.fromEntries(RULES.map((rule) => [rule.id, []]))
  for (const file of scopedFiles()) {
    const src = readFileSync(file, 'utf8')
    for (const rule of RULES) {
      for (const hit of rule.find(src, file)) {
        result[rule.id].push({ file, line: hit.line, text: hit.text })
      }
    }
  }
  return result
}

export function countsOf(violations) {
  return Object.fromEntries(Object.entries(violations).map(([id, hits]) => [id, hits.length]))
}

function reportToConsole(violations) {
  const counts = countsOf(violations)
  for (const rule of RULES) {
    console.log(`${counts[rule.id].toString().padStart(4)}  ${rule.id}  — ${rule.describe}`)
  }
  console.log(`${Object.values(counts).reduce((a, b) => a + b, 0).toString().padStart(4)}  TOTAL`)
}

if (import.meta.url === `file://${process.argv[1].replace(/\\/g, '/')}`) {
  const violations = collectViolations()
  if (process.argv.includes('--json')) {
    console.log(JSON.stringify(countsOf(violations), null, 2))
  } else {
    reportToConsole(violations)
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test .design-sync/check/ds-check.test.mjs`
Expected: PASS, 4 tests.

- [ ] **Step 5: Verify the CLI output by eye**

Run: `node .design-sync/check/ds-check.mjs`
Expected exactly:
```
  69  no-raw-palette  — Tailwind palette literal; use a semantic token
   9  no-bare-button  — bare <button>; use the Button primitive
  11  no-adhoc-input  — ad-hoc styled input; use a shared Input primitive
   0  no-inline-style  — inline style prop; use tokens and Tailwind classes
  89  TOTAL
```

If `no-adhoc-input` shows 0, the brace scanner is not wired. If it shows 7, something reverted to line-based matching. Only 11 is correct.

- [ ] **Step 6: Commit**

```bash
git add .design-sync/check/ds-check.mjs .design-sync/check/ds-check.test.mjs
git commit -m "feat: add ds-check CLI pinned to verified violation counts"
```

---

### Task 5: Baseline ratchet and gate mode

**Files:**
- Create: `.design-sync/check/baseline.json`
- Modify: `.design-sync/check/ds-check.mjs` (add `--gate` handling)
- Test: `.design-sync/check/gate.test.mjs`

**Interfaces:**
- Consumes: `collectViolations`, `countsOf` from `./ds-check.mjs` (Task 4)
- Produces: `evaluateGate(counts, baseline) => {ok: boolean, regressions: Array<{id: string, was: number, now: number}>, improvements: Array<{id: string, was: number, now: number}>}` — pure, no I/O, so it is testable without touching disk.

- [ ] **Step 1: Write the failing test**

Create `.design-sync/check/gate.test.mjs`:

```javascript
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { evaluateGate } from './ds-check.mjs'

test('passes when counts equal the baseline', () => {
  const result = evaluateGate({ 'no-bare-button': 9 }, { 'no-bare-button': 9 })
  assert.equal(result.ok, true)
  assert.deepEqual(result.regressions, [])
  assert.deepEqual(result.improvements, [])
})

test('fails when a count exceeds the baseline', () => {
  const result = evaluateGate({ 'no-bare-button': 10 }, { 'no-bare-button': 9 })
  assert.equal(result.ok, false)
  assert.deepEqual(result.regressions, [{ id: 'no-bare-button', was: 9, now: 10 }])
})

test('passes and reports an improvement when a count drops', () => {
  const result = evaluateGate({ 'no-bare-button': 8 }, { 'no-bare-button': 9 })
  assert.equal(result.ok, true)
  assert.deepEqual(result.improvements, [{ id: 'no-bare-button', was: 9, now: 8 }])
})

test('treats a rule missing from the baseline as a zero ceiling', () => {
  const result = evaluateGate({ 'new-rule': 1 }, {})
  assert.equal(result.ok, false, 'an unbaselined rule must not pass silently')
  assert.deepEqual(result.regressions, [{ id: 'new-rule', was: 0, now: 1 }])
})

test('reports every regression, not just the first', () => {
  const result = evaluateGate(
    { 'no-bare-button': 10, 'no-raw-palette': 70 },
    { 'no-bare-button': 9, 'no-raw-palette': 69 },
  )
  assert.equal(result.regressions.length, 2)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test .design-sync/check/gate.test.mjs`
Expected: FAIL — `evaluateGate` is not exported.

- [ ] **Step 3: Create the baseline file**

Create `.design-sync/check/baseline.json`:

```json
{
  "no-raw-palette": 69,
  "no-bare-button": 9,
  "no-adhoc-input": 11,
  "no-inline-style": 0
}
```

- [ ] **Step 4: Add gate logic to `ds-check.mjs`**

Add this import at the top of `.design-sync/check/ds-check.mjs`, alongside the existing ones:

```javascript
import { readFileSync, writeFileSync, globSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
```

(Replace the existing `node:fs` import line; `writeFileSync` is newly needed.)

Add after `countsOf`:

```javascript
const BASELINE_PATH = join(dirname(fileURLToPath(import.meta.url)), 'baseline.json')

/**
 * Compare counts to the baseline.
 *
 * A rule absent from the baseline has a ceiling of 0, so a newly added rule
 * cannot pass unnoticed. Pure function — the caller does the I/O.
 */
export function evaluateGate(counts, baseline) {
  const regressions = []
  const improvements = []
  for (const [id, now] of Object.entries(counts)) {
    const was = baseline[id] ?? 0
    if (now > was) regressions.push({ id, was, now })
    else if (now < was) improvements.push({ id, was, now })
  }
  return { ok: regressions.length === 0, regressions, improvements }
}
```

Then replace the `if (import.meta.url === ...)` block at the bottom with:

```javascript
function runGate(violations) {
  const counts = countsOf(violations)
  const baseline = JSON.parse(readFileSync(BASELINE_PATH, 'utf8'))
  const { ok, regressions, improvements } = evaluateGate(counts, baseline)

  if (!ok) {
    console.error('Design system check failed — new violations introduced.\n')
    for (const { id, was, now } of regressions) {
      const rule = RULES.find((r) => r.id === id)
      console.error(`  ${id}: ${was} -> ${now}  (${rule?.describe ?? 'unknown rule'})`)
      for (const hit of violations[id].slice(-(now - was))) {
        console.error(`    ${hit.file}:${hit.line}  ${hit.text}`)
      }
    }
    console.error('\nSee .design-sync/north-star.md for the invariants.')
    process.exit(1)
  }

  if (improvements.length > 0) {
    for (const { id, was, now } of improvements) {
      baseline[id] = now
      console.log(`Design system baseline ratcheted: ${id} ${was} -> ${now}`)
    }
    writeFileSync(BASELINE_PATH, `${JSON.stringify(baseline, null, 2)}\n`)
    console.log('Updated .design-sync/check/baseline.json — commit it with your change.')
  }
}

if (import.meta.url === `file://${process.argv[1].replace(/\\/g, '/')}`) {
  const violations = collectViolations()
  if (process.argv.includes('--gate')) runGate(violations)
  else if (process.argv.includes('--json')) console.log(JSON.stringify(countsOf(violations), null, 2))
  else reportToConsole(violations)
}
```

The slice `violations[id].slice(-(now - was))` shows only the newly added violations rather than all 89, so the message stays readable.

- [ ] **Step 5: Run test to verify it passes**

Run: `node --test .design-sync/check/gate.test.mjs`
Expected: PASS, 5 tests.

- [ ] **Step 6: Verify the gate passes on the clean tree**

Run: `node .design-sync/check/ds-check.mjs --gate; echo "exit=$?"`
Expected: no output, `exit=0`.

- [ ] **Step 7: Verify the gate catches a real regression**

```bash
# Introduce one violation
printf '\nexport const TEMP = "bg-green-600"\n' >> web/src/features/plan/PlanPage.tsx
node .design-sync/check/ds-check.mjs --gate; echo "exit=$?"
```
Expected: exit=1, and output naming `no-raw-palette: 69 -> 70` plus the `PlanPage.tsx` line. Confirm it lists **one** location, not 70.

```bash
# Revert
git checkout -- web/src/features/plan/PlanPage.tsx
node .design-sync/check/ds-check.mjs --gate; echo "exit=$?"
```
Expected: `exit=0`.

- [ ] **Step 8: Verify the ratchet drops on improvement**

```bash
# Temporarily lower a real count by deleting one bare button's opening tag
node -e "const f='web/src/features/state/StatePage.tsx';const s=require('fs').readFileSync(f,'utf8');require('fs').writeFileSync(f,s.replace('<button','<Button'))"
node .design-sync/check/ds-check.mjs --gate
cat .design-sync/check/baseline.json
```
Expected: prints `no-bare-button 9 -> 8`, and `baseline.json` now reads `"no-bare-button": 8`.

```bash
# Revert both the source and the baseline
git checkout -- web/src/features/state/StatePage.tsx .design-sync/check/baseline.json
node .design-sync/check/ds-check.mjs --gate; echo "exit=$?"
```
Expected: `exit=0`, baseline back to 9.

- [ ] **Step 9: Commit**

```bash
git add .design-sync/check/baseline.json .design-sync/check/ds-check.mjs .design-sync/check/gate.test.mjs
git commit -m "feat: add baseline ratchet and gate mode to ds-check"
```

---

### Task 6: Tier 2 staleness stamp

Tier 2 cannot run in a hook — it needs both servers, a browser, and model judgment. What a hook *can* do is notice the review is overdue. This task builds that check; it never blocks.

**Files:**
- Create: `.design-sync/check/lib/stamp.mjs`
- Test: `.design-sync/check/lib/stamp.test.mjs`

**Interfaces:**
- Consumes: `scopedFiles` from `./files.mjs` (Task 4) — **not** from `ds-check.mjs`, which would create an import cycle
- Produces:
  - `extractClassNames(src: string) => string[]` — every `className` attribute value, quoted or braced
  - `currentStamp() => string` — 16-char sha256 prefix over all in-scope className values
  - `readStamp() => string | null` — the recorded stamp, or `null` if never reviewed
  - `writeStamp(hash: string) => void` — records a stamp at `.design-sync/check/review-stamp.json`
  - `reviewIsStale() => boolean`

- [ ] **Step 1: Write the failing test**

Create `.design-sync/check/lib/stamp.test.mjs`:

```javascript
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { extractClassNames, currentStamp } from './stamp.mjs'

test('extracts a quoted className', () => {
  assert.deepEqual(extractClassNames('<div className="p-4 gap-2" />'), ['"p-4 gap-2"'])
})

test('extracts a braced template-literal className', () => {
  const values = extractClassNames('<div className={`p-4 ${x}`} />')
  assert.equal(values.length, 1)
  assert.match(values[0], /p-4/)
})

test('extracts a braced call expression className', () => {
  const values = extractClassNames('<div className={cn("p-4", other)} />')
  assert.equal(values.length, 1)
  assert.match(values[0], /cn\("p-4", other\)/)
})

test('handles nested braces inside a braced className', () => {
  const values = extractClassNames('<div className={`w-${sizes[{a:1}.a]}`} />')
  assert.equal(values.length, 1, 'must not end at the first inner closing brace')
})

test('collapses whitespace so reformatting does not count as visual change', () => {
  const inline = extractClassNames('<div className={cn("a", "b")} />')
  const wrapped = extractClassNames('<div className={cn(\n  "a",\n  "b",\n)} />')
  assert.equal(inline[0].replace(/,\s*\)/, ')'), wrapped[0].replace(/,\s*\)/, ')'))
})

test('ignores non-className attributes', () => {
  assert.deepEqual(extractClassNames('<div id="p-4" data-x="gap-2" />'), [])
})

test('currentStamp is stable across repeated calls', () => {
  assert.equal(currentStamp(), currentStamp())
})

test('currentStamp is a 16-char hex digest', () => {
  assert.match(currentStamp(), /^[0-9a-f]{16}$/)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test .design-sync/check/lib/stamp.test.mjs`
Expected: FAIL — `Cannot find module` for `stamp.mjs`.

- [ ] **Step 3: Write minimal implementation**

Create `.design-sync/check/lib/stamp.mjs`:

```javascript
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { scopedFiles } from './files.mjs'

const STAMP_PATH = join(dirname(fileURLToPath(import.meta.url)), '..', 'review-stamp.json')

/**
 * Every className attribute value in `src`, quoted or braced.
 *
 * Only className is hashed, not whole files: a logic refactor must not make a
 * visual review overdue, or the notice gets ignored within a week. Changing
 * `p-4` to `p-6` must.
 */
export function extractClassNames(src) {
  const values = []
  const attr = /className=/g
  let match
  while ((match = attr.exec(src))) {
    const start = match.index + match[0].length
    if (src[start] === '"') {
      const end = src.indexOf('"', start + 1)
      values.push(src.slice(start, end + 1))
    } else if (src[start] === '{') {
      values.push(src.slice(start, findBraceEnd(src, start) + 1).replace(/\s+/g, ' '))
    }
  }
  return values
}

/** Index of the brace closing the one at `start`. */
function findBraceEnd(src, start) {
  let depth = 0
  for (let i = start; i < src.length; i++) {
    if (src[i] === '{') depth++
    else if (src[i] === '}' && --depth === 0) return i
  }
  return src.length - 1
}

export function currentStamp() {
  const parts = scopedFiles().map((file) => `${file}\n${extractClassNames(readFileSync(file, 'utf8')).join('\n')}`)
  return createHash('sha256').update(parts.join('\n')).digest('hex').slice(0, 16)
}

export function readStamp() {
  if (!existsSync(STAMP_PATH)) return null
  return JSON.parse(readFileSync(STAMP_PATH, 'utf8')).stamp ?? null
}

export function writeStamp(hash) {
  writeFileSync(STAMP_PATH, `${JSON.stringify({ stamp: hash }, null, 2)}\n`)
}

export function reviewIsStale() {
  return readStamp() !== currentStamp()
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test .design-sync/check/lib/stamp.test.mjs`
Expected: PASS, 8 tests.

- [ ] **Step 5: Verify the behaviour that justifies hashing className only**

```bash
node -e "import('./.design-sync/check/lib/stamp.mjs').then(m=>console.log('base   ', m.currentStamp()))"
printf '\nconst unusedLogicChange = 42\n' >> web/src/features/state/StatePage.tsx
node -e "import('./.design-sync/check/lib/stamp.mjs').then(m=>console.log('logic  ', m.currentStamp()))"
git checkout -- web/src/features/state/StatePage.tsx
node -e "const fs=require('fs');const f='web/src/features/state/StatePage.tsx';fs.writeFileSync(f,fs.readFileSync(f,'utf8').replace('space-y-6','space-y-8'))"
node -e "import('./.design-sync/check/lib/stamp.mjs').then(m=>console.log('style  ', m.currentStamp()))"
git checkout -- web/src/features/state/StatePage.tsx
```

Expected: `base` and `logic` are **identical**; `style` **differs**. If the logic edit changes the hash, the extractor is hashing more than className and the notice will fire constantly.

- [ ] **Step 6: Commit**

```bash
git add .design-sync/check/lib/stamp.mjs .design-sync/check/lib/stamp.test.mjs
git commit -m "feat: track Tier 2 review staleness via className stamp"
```

---

### Task 7: Stop hook wiring

**Files:**
- Create: `.claude/settings.json`
- Modify: `.design-sync/check/ds-check.mjs` (emit the staleness notice in `--gate`)
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: `node .design-sync/check/ds-check.mjs --gate` (Task 5), `reviewIsStale` from `./lib/stamp.mjs` (Task 6)
- Produces: nothing consumed by later tasks

- [ ] **Step 1: Create the project settings file**

`.claude/settings.json` does not exist yet — only `.claude/settings.local.json`, which is personal and must not be edited here. Create `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node .design-sync/check/ds-check.mjs --gate"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Emit the staleness notice from `--gate`**

In `.design-sync/check/ds-check.mjs`, add the import:

```javascript
import { reviewIsStale } from './lib/stamp.mjs'
```

Then, at the end of `runGate`, after the improvements block:

```javascript
  // Advisory only — never exits non-zero. Tier 2 needs servers, a browser and
  // judgment, so a hook can report that review is overdue but cannot perform it.
  if (reviewIsStale()) {
    console.log('Tier 2 visual review is stale — page styling changed since the last /ds-review.')
  }
```

Note this sits *after* the `process.exit(1)` in the regression branch by design: when Tier 1 has failed, that is the actionable problem, and a second message competing for attention makes the first easier to skim past.

- [ ] **Step 3: Verify the hook command runs from the project root**

Run: `node .design-sync/check/ds-check.mjs --gate; echo "exit=$?"`
Expected: `exit=0`, with the staleness line printed (no stamp exists yet, so review is stale until Task 8 runs). The `globSync` scope is repo-relative, so the hook depends on the working directory being the project root.

- [ ] **Step 4: Add the north star pointer to `CLAUDE.md`**

Append this section to `CLAUDE.md`, immediately after the `### Frontend Structure` section:

```markdown
### Design System

Before writing or editing anything under `web/src/features/`, read `.design-sync/north-star.md`. It holds every design invariant and is the single source for them.

Tier 1 invariants are enforced automatically: a `Stop` hook runs `node .design-sync/check/ds-check.mjs --gate` and fails the turn if any violation count rises above `.design-sync/check/baseline.json`. Fix new violations rather than raising the baseline — the baseline only ever moves down, automatically, and a manual increase is a reviewable change requiring justification.

Tier 2 invariants are visual and cannot be linted, so they are not gated. Instead the hook reports when `/ds-review` is overdue — that is, when `className` values in `web/src/features/` changed since the last review.

**When the hook reports Tier 2 is stale, offer the review** — do not silently skip it and do not run it unprompted. Raise it at a natural boundary: before committing or pushing, or when reporting a chunk of visual work complete. Say that Tier 1 passed, that Tier 2 is overdue, and ask whether to run `/ds-review`. It needs both servers and a browser session, so it is the user's call, but the offer is not optional.

To check on demand: `node .design-sync/check/ds-check.mjs`
```

- [ ] **Step 5: Verify the hook actually fires**

An unwired hook is silent and looks identical to a passing one, so this must be confirmed directly rather than assumed.

Temporarily break the gate so a firing hook is unmistakable:

```bash
printf '\nexport const TEMP = "bg-green-600"\n' >> web/src/features/plan/PlanPage.tsx
```

End a turn normally. Expected: the Stop hook fails and the `no-raw-palette: 69 -> 70` message plus the `PlanPage.tsx` location appear as feedback. If the turn ends with no complaint, the hook is not wired — check that `.claude/settings.json` is valid JSON and that the session picked it up.

Then revert:

```bash
git checkout -- web/src/features/plan/PlanPage.tsx
```

- [ ] **Step 6: Commit**

```bash
git add .claude/settings.json .design-sync/check/ds-check.mjs CLAUDE.md
git commit -m "feat: run design system gate on every turn via Stop hook"
```

---

### Task 8: `/ds-review` visual review skill

**Files:**
- Create: `.claude/skills/ds-review/SKILL.md`

**Interfaces:**
- Consumes: `.design-sync/north-star.md` Tier 2 invariants (Task 1); the existing `run-app` skill at `.claude/skills/run-app/SKILL.md`; `currentStamp`/`writeStamp` from `.design-sync/check/lib/stamp.mjs` (Task 6)
- Produces: `.design-sync/.cache/review/<Page>.grade.json` files and `.design-sync/check/review-stamp.json`

- [ ] **Step 1: Write the skill**

Match the frontmatter format of the existing `run-app` skill. Create `.claude/skills/ds-review/SKILL.md`:

```markdown
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
```

- [ ] **Step 2: Verify frontmatter parses and the skill is discoverable**

Run: `head -4 .claude/skills/ds-review/SKILL.md`
Expected: a `---` fenced block with `name: ds-review` and a `description:` line, matching the `run-app` format.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/ds-review/SKILL.md
git commit -m "feat: add ds-review skill for Tier 2 visual design checks"
```

---

### Task 9: Full-suite verification

**Files:**
- Modify: none (verification only)

**Interfaces:**
- Consumes: everything from Tasks 1–7
- Produces: nothing

- [ ] **Step 1: Run every checker test together**

Run: `node --test .design-sync/check/`
Expected: PASS, 36 tests total (7 scanner + 12 rules + 4 CLI + 5 gate + 8 stamp), 0 failures.

- [ ] **Step 2: Confirm the frontend test suite is unaffected**

Run: `cd web && npm test -- --run`
Expected: same pass count as before this plan. Nothing here touches `web/src`.

- [ ] **Step 3: Confirm the backend suite is unaffected**

Run: `uv run pytest tests/ -q`
Expected: unchanged. This plan adds no Python.

- [ ] **Step 4: Confirm the working tree is clean**

Run: `git status --porcelain`
Expected: empty. In particular `baseline.json` and `review-stamp.json` must be unmodified — if either changed, an earlier verification step was not reverted.

- [ ] **Step 5: Confirm all spec verification criteria are met**

Walk the Verification section of the spec and confirm each:

1. Reports 69 / 9 / 11 / 0 — Task 4 Step 5
2. A deliberate violation fails the gate naming only that line — Task 5 Step 7
3. Fixing a violation ratchets the baseline down — Task 5 Step 8
4. Raising a baseline is a hand edit, not automatic — verify by inspection: `evaluateGate` only writes on `improvements`, never on `regressions`
5. A real Stop event fires the hook — Task 7 Step 5
6. Tier 2 staleness is advisory: confirm `runGate` prints the notice without affecting exit code — Task 7 Step 3 showed `exit=0` while stale
7. A logic edit does not mark review stale; a style edit does — Task 6 Step 5

- [ ] **Step 6: Commit any outstanding plan updates**

```bash
git add plan/issue-0-design-system-north-star/plan.md
git commit -m "docs: mark design system north star plan complete"
```

---

## Self-review notes

**Spec coverage.** Every spec section maps to a task: north star document → Task 1; Tier 1 rules and the brace-scanner constraint → Tasks 2–4; baseline ratchet → Task 5; Tier 2 staleness tracking → Task 6; Stop hook and `CLAUDE.md` → Task 7; Tier 2 review → Task 8; the spec's verification criteria → Task 9 Step 5.

**Deliberately out of scope.** Extracting an `Input` primitive (invariant 3 has nothing to migrate toward — recorded in the north star's Known gaps), migrating the 89 existing violations, and auditing `web/src/components/` against invariant 1.

**Risk carried forward.**

- `no-raw-palette` cannot see inside template literals, so `PlanPage.tsx:83` is invisible to it. Tier 2 is the only backstop.
- Staleness tracking removes *forgetting* as a failure mode for Tier 2, not *declining*. A user who answers "not now" every time ends up where they started. This was chosen deliberately over gating commits, which would buy compliance at the cost of a `--no-verify` habit that would undermine Tier 1's gate as well.
- Stamping without actually reviewing silences the notice permanently. Task 8's skill says so explicitly, but nothing enforces it — Tier 2 rests on good faith by construction.
