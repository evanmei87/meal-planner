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
